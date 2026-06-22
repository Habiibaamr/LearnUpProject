from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_student
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.course import Course
from app.models.course_offering import CourseOffering
from app.models.course_prerequisite import CoursePrerequisite
from app.models.course_registration import CourseRegistration
from app.models.department import Department
from app.models.student import Student
from app.models.user import User
from app.schemas.chat import (
    ChatMessageOut,
    ChatRequest,
    ChatResponse,
    ChatSessionOut,
    ChatSourceItem,
    ChatStartResponse,
    ChatbotHistoryResponse,
    ChatbotMessageRequest,
    ChatbotMessageResponse,
)
from app.services import registration_rules
from app.services.academic_metrics import (
    DEMO_LEVEL_GRADES,
    GRADE_POINTS,
    LEVEL_TO_PREVIOUS_COURSE_CODES,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/start", response_model=ChatStartResponse)
def start_chat_session(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    session = ChatSession(user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return ChatStartResponse(session_id=session.id, started_at=session.started_at)


@router.get("/my-sessions", response_model=List[ChatSessionOut])
def list_my_chat_sessions(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.id.desc())
        .all()
    )
    return [ChatSessionOut.model_validate(s) for s in rows]


def _get_owned_session(
    db: Session, session_id: int, user_id: int
) -> ChatSession:
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This chat session does not belong to you",
        )
    return session


def _get_student_academic_context(current_user: User, db: Session) -> dict:
    student = (
        db.query(Student)
        .filter(Student.user_id == current_user.id)
        .first()
    )
    if student is None:
        return {
            "full_name": current_user.full_name,
            "email": current_user.email,
            "university_id": current_user.university_id,
            "department": None,
            "level": None,
            "cgpa": None,
            "passed_credit_hours": 0,
            "enrolled_courses": [],
            "completed_courses": [],
            "grades": [],
            "available_courses": [],
            "locked_courses": [],
        }

    department = (
        db.query(Department)
        .filter(Department.id == student.department_id)
        .first()
        if student.department_id is not None
        else None
    )
    registrations = (
        db.query(CourseRegistration)
        .filter(CourseRegistration.student_id == student.id)
        .order_by(CourseRegistration.id.asc())
        .all()
    )
    offerings = {
        offering.id: offering
        for offering in db.query(CourseOffering).all()
    }
    courses = {
        course.id: course
        for course in db.query(Course).all()
    }

    enrolled_courses = []
    completed_courses = []
    grades = []
    active_course_ids = set()
    passed_course_ids = set()

    for registration in registrations:
        offering = offerings.get(registration.course_offering_id)
        course = courses.get(offering.course_id) if offering is not None else None
        if course is None:
            continue

        course_record = {
            "course_id": course.id,
            "course_offering_id": offering.id,
            "course_code": course.course_code,
            "course_title": course.title,
            "credit_hours": course.credit_hours,
            "semester_id": offering.semester_id,
            "status": registration.status,
        }
        if registration.status in registration_rules.ACTIVE_REGISTRATION_STATUSES:
            active_course_ids.add(course.id)
            enrolled_courses.append(course_record)

        is_completed = (
            registration.status == "completed"
            or registration.is_passed is not None
            or bool(registration.final_grade)
        )
        if is_completed:
            completed_record = {
                **course_record,
                "final_grade": registration.final_grade,
                "is_passed": registration.is_passed,
            }
            completed_courses.append(completed_record)
            if registration.is_passed is True or (
                registration.status == "completed"
                and registration.is_passed is not False
            ):
                passed_course_ids.add(course.id)
            if registration.final_grade:
                grades.append(completed_record)

    grade_codes = {item["course_code"] for item in grades}
    completed_codes = {item["course_code"] for item in completed_courses}
    demo_codes = LEVEL_TO_PREVIOUS_COURSE_CODES.get(student.level or 1, [])
    for course_code in demo_codes:
        if course_code in grade_codes:
            continue
        course = next(
            (row for row in courses.values() if row.course_code == course_code),
            None,
        )
        grade = DEMO_LEVEL_GRADES.get(course_code)
        if course is None or grade is None:
            continue
        demo_record = {
            "course_id": course.id,
            "course_offering_id": None,
            "course_code": course.course_code,
            "course_title": course.title,
            "credit_hours": course.credit_hours,
            "semester_id": None,
            "status": "completed",
            "final_grade": grade,
            "is_passed": grade != "F",
            "source": "demo_academic_history",
        }
        grades.append(demo_record)
        if course_code not in completed_codes:
            completed_courses.append(demo_record)
            completed_codes.add(course_code)
        if grade != "F":
            passed_course_ids.add(course.id)

    cgpa = student.cgpa
    passed_credit_hours = student.passed_credit_hours or 0
    if grades:
        total_points = sum(
            GRADE_POINTS.get(str(item["final_grade"]).upper(), 0.0)
            * int(item["credit_hours"] or 0)
            for item in grades
        )
        total_hours = sum(int(item["credit_hours"] or 0) for item in grades)
        calculated_cgpa = round(total_points / total_hours, 2) if total_hours else None
        if cgpa is None:
            cgpa = calculated_cgpa
        if not passed_credit_hours:
            passed_credit_hours = sum(
                int(item["credit_hours"] or 0)
                for item in completed_courses
                if item.get("is_passed") is not False
            )

    prerequisite_rows = db.query(CoursePrerequisite).all()
    prerequisites_by_course: dict[int, list[int]] = {}
    for row in prerequisite_rows:
        prerequisites_by_course.setdefault(row.course_id, []).append(
            row.prerequisite_course_id
        )

    offerings_by_course: dict[int, CourseOffering] = {}
    for offering in sorted(offerings.values(), key=lambda item: item.id, reverse=True):
        offerings_by_course.setdefault(offering.course_id, offering)

    available_courses = []
    locked_courses = []
    for course in courses.values():
        if student.faculty_id is not None and course.faculty_id != student.faculty_id:
            continue
        offering = offerings_by_course.get(course.id)
        if offering is None:
            continue
        record = {
            "course_id": course.id,
            "course_offering_id": offering.id,
            "course_code": course.course_code,
            "course_title": course.title,
            "credit_hours": course.credit_hours,
        }
        if course.id in active_course_ids or course.id in passed_course_ids:
            continue
        if (
            student.level is not None
            and course.level is not None
            and course.level < student.level
        ):
            continue

        missing_prerequisites = [
            prerequisite_id
            for prerequisite_id in prerequisites_by_course.get(course.id, [])
            if prerequisite_id not in passed_course_ids
        ]
        if (
            student.level is not None
            and course.level is not None
            and course.level > student.level
        ):
            locked_courses.append({**record, "reason": "Level not reached"})
        elif missing_prerequisites:
            missing_codes = [
                courses[item].course_code
                for item in missing_prerequisites
                if item in courses
            ]
            locked_courses.append(
                {
                    **record,
                    "reason": "Missing prerequisites: " + ", ".join(missing_codes),
                }
            )
        else:
            available_courses.append(record)

    return {
        "student_id": student.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "university_id": current_user.university_id,
        "department": department.name if department is not None else None,
        "level": student.level,
        "cgpa": cgpa,
        "passed_credit_hours": passed_credit_hours,
        "enrolled_courses": enrolled_courses,
        "completed_courses": completed_courses,
        "grades": grades,
        "available_courses": available_courses,
        "locked_courses": locked_courses,
    }


def _format_course_list(courses: list[dict], include_grade: bool = False) -> str:
    if not courses:
        return "None recorded."
    rows = []
    for course in courses:
        label = f"{course['course_code']} - {course['course_title']}"
        if include_grade:
            label += f": {course.get('final_grade') or 'Pending'}"
        rows.append(f"- {label}")
    return "\n".join(rows)


def _build_chat_context(context: dict) -> str:
    return "\n".join(
        [
            f"Full name: {context.get('full_name')}",
            f"Email: {context.get('email')}",
            f"University ID: {context.get('university_id')}",
            f"Department: {context.get('department') or 'Not recorded'}",
            f"Level: {context.get('level') or 'Not recorded'}",
            f"CGPA: {context.get('cgpa') if context.get('cgpa') is not None else 'Not recorded'}",
            f"Passed credit hours: {context.get('passed_credit_hours', 0)}",
            "Enrolled courses:\n" + _format_course_list(context["enrolled_courses"]),
            "Completed courses and grades:\n"
            + _format_course_list(context["grades"], include_grade=True),
            "Available courses:\n" + _format_course_list(context["available_courses"]),
            "Locked courses:\n" + _format_course_list(context["locked_courses"]),
        ]
    )


def _build_database_fallback(question: str, context: dict) -> str:
    normalized = (question or "").strip().lower()
    if any(term in normalized for term in ("grade", "result", "marks")):
        return (
            f"Here are the grades in your LearnUp academic record:\n"
            f"{_format_course_list(context['grades'], include_grade=True)}\n"
            f"CGPA: {context.get('cgpa') if context.get('cgpa') is not None else 'Not recorded'}"
        )
    if "gpa" in normalized or "cgpa" in normalized:
        cgpa = context.get("cgpa")
        return (
            f"Your current CGPA is {cgpa:.2f}."
            if isinstance(cgpa, (int, float))
            else "Your CGPA is not recorded yet."
        )
    if "enrolled" in normalized or "registered" in normalized:
        return (
            "Your currently enrolled courses are:\n"
            + _format_course_list(context["enrolled_courses"])
        )
    if any(
        phrase in normalized
        for phrase in ("can i take", "available course", "courses can i")
    ):
        return (
            "Based on your level, prerequisites, passed courses, and current "
            "enrollments, you can take:\n"
            + _format_course_list(context["available_courses"])
        )
    if "progress" in normalized:
        return (
            f"You are currently at Level {context.get('level') or 'not recorded'} "
            f"with {context.get('passed_credit_hours', 0)} passed credit hours and "
            f"a CGPA of {context.get('cgpa') if context.get('cgpa') is not None else 'not recorded'}."
        )
    return (
        f"I found your LearnUp academic record, {context.get('full_name')}. "
        "You can ask me to show your grades, GPA, enrolled courses, or available courses."
    )


def _detect_intent(message: str) -> str:
    """Detect the intent of the user's message."""
    normalized = (message or "").strip().lower()
    _log.info("active_chat_handler_called: true")
    _log.info("message_text: %s", normalized)
    
    # Check for GPA questions
    if "gpa" in normalized or "cgpa" in normalized:
        _log.info("detected_intent: gpa")
        return "gpa"
    
    # Check for grades/results questions
    if any(term in normalized for term in ("grade", "result", "marks", "semester result")):
        _log.info("detected_intent: grades")
        return "grades"
    
    # Check for enrolled courses questions
    if any(term in normalized for term in ("enrolled", "my course", "registered")) and "course" in normalized:
        _log.info("detected_intent: enrolled_courses")
        return "enrolled_courses"
    
    # Check for available courses questions - more flexible matching
    if any(term in normalized for term in ("available", "can i take", "what can i", "course board", "courses can i")) and "course" in normalized:
        _log.info("detected_intent: available_courses")
        return "available_courses"
    
    _log.info("detected_intent: general")
    return "general"


@router.post("/{session_id:int}/message", response_model=ChatResponse)
def send_chat_message(
    session_id: int,
    body: ChatRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    from app.services import chatbot_service
    import os

    _log.info("=== ACTIVE CHAT MESSAGE HANDLER CALLED ===")
    _log.info("session_id: %s", session_id)
    _get_owned_session(db, session_id, current_user.id)

    # Debug logs
    _log.info("user_id: %s", current_user.id)
    _log.info("user_email: %s", current_user.email)
    _log.info("user_role: %s", current_user.role)
    
    user_msg = ChatMessage(
        session_id=session_id,
        sender_type="user",
        message_text=body.message,
    )
    db.add(user_msg)
    db.flush()
    _log.info("saved_user_message_id: %s", user_msg.id)

    academic_context = _get_student_academic_context(current_user, db)
    
    # Debug logs for student data
    _log.info("student_id: %s", academic_context.get("student_id"))
    _log.info("student_level: %s", academic_context.get("level"))
    _log.info("student_cgpa: %s", academic_context.get("cgpa"))
    _log.info("registrations_count: %d", len(academic_context.get("enrolled_courses", [])) + len(academic_context.get("completed_courses", [])))
    _log.info("grades_count: %d", len(academic_context.get("grades", [])))
    _log.info("enrolled_courses_count: %d", len(academic_context.get("enrolled_courses", [])))
    _log.info("available_courses_count: %d", len(academic_context.get("available_courses", [])))
    
    # Detect intent
    intent = _detect_intent(body.message)
    _log.info("intent detected: %s", intent)
    
    # Direct database answers for specific intents
    if intent in ("gpa", "grades", "enrolled_courses", "available_courses"):
        _log.info("used_sis_direct_answer: true")
        _log.info("used_advising_kb: false")
        _log.info("returned_kb: SIS")
        
        direct_answer = _build_database_fallback(body.message, academic_context)
        stored_text = direct_answer
        assistant_msg = ChatMessage(
            session_id=session_id,
            sender_type="assistant",
            message_text=stored_text,
        )
        db.add(assistant_msg)
        db.commit()
        _log.info("saved_assistant_message_id: %s", assistant_msg.id)
        
        # Count messages after save
        messages_count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
        _log.info("messages_count_after_save: %d", messages_count)
        
        return ChatResponse(
            session_id=session_id,
            user_message=body.message,
            assistant_response=direct_answer,
            kb="SIS",
            sources=[],
        )
    
    # For general questions, use OpenAI with student context
    _log.info("used_sis_direct_answer: false")
    _log.info("used_advising_kb: true")
    
    api_key_exists = bool(os.getenv("OPENAI_API_KEY", "").strip())
    _log.info("OPENAI_API_KEY exists: %s", str(api_key_exists).lower())
    
    turn = chatbot_service.generate_chatbot_reply(
        body.message,
        student_context=_build_chat_context(academic_context),
        fallback_text=_build_database_fallback(body.message, academic_context),
    )
    
    _log.info("used OpenAI: %s", str(turn.kb != "").lower())
    _log.info("used fallback: %s", str(turn.kb == "").lower())
    _log.info("returned_kb: %s", turn.kb or "None")
    
    stored_text = chatbot_service.format_stored_assistant_message(turn)
    assistant_msg = ChatMessage(
        session_id=session_id,
        sender_type="assistant",
        message_text=stored_text,
    )
    db.add(assistant_msg)
    db.commit()
    _log.info("saved_assistant_message_id: %s", assistant_msg.id)
    
    # Count messages after save
    messages_count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
    _log.info("messages_count_after_save: %d", messages_count)

    return ChatResponse(
        session_id=session_id,
        user_message=body.message,
        assistant_response=turn.text,
        kb=turn.kb or None,
        sources=[ChatSourceItem(id=s.get("id"), title=s.get("title")) for s in turn.sources],
    )


@router.get("/{session_id:int}/messages", response_model=List[ChatMessageOut])
def list_session_messages(
    session_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    _log.info("=== GET MESSAGES HANDLER CALLED ===")
    _log.info("user_id: %s", current_user.id)
    _log.info("requested_session_id: %s", session_id)
    
    _get_owned_session(db, session_id, current_user.id)
    
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    
    _log.info("messages_count_for_session: %d", len(rows))
    
    return [ChatMessageOut.model_validate(m) for m in rows]


@router.post("/chatbot/message", response_model=ChatbotMessageResponse)
def send_chatbot_message(
    body: ChatbotMessageRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    from app.services import chatbot_service

    session = None
    if body.session_id is not None:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == body.session_id)
            .first()
        )
        if session is None or session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )
    else:
        session = ChatSession(user_id=current_user.id)
        db.add(session)
        db.flush()

    user_msg = ChatMessage(
        session_id=session.id,
        sender_type="user",
        message_text=body.message,
    )
    db.add(user_msg)
    db.flush()

    academic_context = _get_student_academic_context(current_user, db)
    reply = chatbot_service.generate_chatbot_reply(
        body.message,
        student_context=_build_chat_context(academic_context),
        fallback_text=_build_database_fallback(body.message, academic_context),
    )
    assistant_text = reply.text.strip() if reply.text else (
        "I can help with academic advising, but the AI service is not configured yet. "
        "Please contact your academic advisor."
    )
    assistant_msg = ChatMessage(
        session_id=session.id,
        sender_type="ai",
        message_text=assistant_text,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatbotMessageResponse(
        session_id=session.id,
        reply=assistant_text,
        created_at=assistant_msg.created_at,
    )


@router.get("/chatbot/history", response_model=ChatbotHistoryResponse)
def get_chatbot_history(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.id.desc())
        .first()
    )
    if session is None:
        return ChatbotHistoryResponse(session_id=None, messages=[])

    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    return ChatbotHistoryResponse(
        session_id=session.id,
        messages=[ChatMessageOut.model_validate(row) for row in rows],
    )
