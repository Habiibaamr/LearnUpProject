import logging
import re
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_instructor
from app.models.course import Course
from app.models.course_instructor import CourseInstructor
from app.models.course_offering import CourseOffering
from app.models.course_prerequisite import CoursePrerequisite
from app.models.course_registration import CourseRegistration
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.instructor import Instructor
from app.models.lecture_group import LectureGroup
from app.models.section_group import SectionGroup
from app.models.semester import Semester
from app.models.student import Student
from app.models.user import User
from app.services import registration_rules
from app.services.academic_metrics import recalculate_student_academic_metrics

router = APIRouter(prefix="/faculty", tags=["faculty"])
DEFAULT_COURSE_CAPACITY = 40
ROSTER_REGISTRATION_STATUSES = (
    *registration_rules.ACTIVE_REGISTRATION_STATUSES,
    "completed",
)
_log = logging.getLogger("uvicorn.error")


class EnrollStudentsRequest(BaseModel):
    student_ids: list[int] = Field(min_length=1)


def _get_instructor(db: Session, current_user: User) -> Instructor:
    instructor = (
        db.query(Instructor)
        .filter(Instructor.user_id == current_user.id)
        .first()
    )
    if instructor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor profile not found",
        )
    return instructor


def _get_department_name(db: Session, department_id: int | None) -> str | None:
    if department_id is None:
        return None
    department = (
        db.query(Department)
        .filter(Department.id == department_id)
        .first()
    )
    return department.name if department is not None else None


def _get_faculty_name(db: Session, faculty_id: int | None) -> str | None:
    if faculty_id is None:
        return None
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    return faculty.name if faculty is not None else None


def _semester_number(semester: Semester | None, semester_id: int) -> int:
    match = re.search(r"\d+", semester.name if semester is not None else "")
    if match:
        return int(match.group())
    return semester_id


def _course_level(course: Course, semester_number: int) -> int | None:
    if course.level is not None:
        return int(course.level)
    if 1 <= semester_number <= 8:
        return ((semester_number - 1) // 2) + 1
    return None


def _academic_year(start_date: date | None) -> str | None:
    if start_date is None:
        return None
    start_year = start_date.year if start_date.month >= 9 else start_date.year - 1
    return f"{start_year}/{start_year + 1}"


def _term_name(semester_number: int) -> str | None:
    if semester_number < 1:
        return None
    return "Fall" if semester_number % 2 == 1 else "Spring"


def _offering_capacity(db: Session, offering_id: int) -> int:
    lecture_groups = (
        db.query(LectureGroup)
        .filter(LectureGroup.course_offering_id == offering_id)
        .all()
    )
    lecture_capacity = sum(int(group.capacity or 0) for group in lecture_groups)
    if lecture_capacity:
        return lecture_capacity

    section_groups = (
        db.query(SectionGroup)
        .filter(SectionGroup.course_offering_id == offering_id)
        .all()
    )
    section_capacity = sum(int(group.capacity or 0) for group in section_groups)
    return section_capacity or DEFAULT_COURSE_CAPACITY


def _get_assigned_offering(
    db: Session,
    instructor_id: int,
    course_offering_id: int,
) -> tuple[CourseOffering, Course, Semester | None]:
    offering = (
        db.query(CourseOffering)
        .filter(CourseOffering.id == course_offering_id)
        .first()
    )
    if offering is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course offering not found",
        )

    assignment = (
        db.query(CourseInstructor)
        .filter(
            CourseInstructor.instructor_id == instructor_id,
            CourseInstructor.course_offering_id == course_offering_id,
        )
        .first()
    )
    _log.info("FACULTY CURRENT INSTRUCTOR ID %s", instructor_id)
    _log.info("FACULTY REQUESTED COURSE OFFERING ID %s", course_offering_id)
    _log.info("FACULTY MATCHING COURSE INSTRUCTOR ROW %s", assignment)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This course offering is not assigned to the logged-in faculty member",
        )

    course = db.query(Course).filter(Course.id == offering.course_id).first()
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found for this offering",
        )
    semester = (
        db.query(Semester)
        .filter(Semester.id == offering.semester_id)
        .first()
    )
    return offering, course, semester


def _active_registration_count(db: Session, course_offering_id: int) -> int:
    return (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.course_offering_id == course_offering_id,
            CourseRegistration.status.in_(
                registration_rules.ACTIVE_REGISTRATION_STATUSES
            ),
        )
        .count()
    )


def _course_payload(
    db: Session,
    offering: CourseOffering,
    course: Course,
    semester: Semester | None,
) -> dict:
    semester_number = _semester_number(semester, offering.semester_id)
    capacity = _offering_capacity(db, offering.id)
    current_enrolled_count = _active_registration_count(db, offering.id)
    return {
        "course_offering_id": offering.id,
        "course_id": course.id,
        "course_code": course.course_code,
        "course_title": course.title,
        "credit_hours": course.credit_hours,
        "semester_id": offering.semester_id,
        "semester_name": semester.name if semester is not None else None,
        "academic_year": _academic_year(
            semester.start_date if semester is not None else None
        ),
        "term": _term_name(semester_number),
        "level": _course_level(course, semester_number),
        "department_id": course.department_id,
        "department_name": _get_department_name(db, course.department_id),
        "capacity": capacity,
        "status": offering.status,
        "current_enrolled_count": current_enrolled_count,
        "enrolled_students_count": current_enrolled_count,
        "remaining_seats": max(0, capacity - current_enrolled_count),
    }


def _missing_prerequisite_codes(
    db: Session,
    student: Student,
    course: Course,
) -> list[str]:
    prerequisite_rows = (
        db.query(CoursePrerequisite)
        .filter(CoursePrerequisite.course_id == course.id)
        .all()
    )
    if not prerequisite_rows:
        return []

    has_transcript_records = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.student_id == student.id,
            CourseRegistration.status == "completed",
        )
        .first()
        is not None
    )
    missing_codes: list[str] = []
    for row in prerequisite_rows:
        if registration_rules.has_passed_course(
            db,
            student.id,
            row.prerequisite_course_id,
        ):
            continue

        prerequisite = (
            db.query(Course)
            .filter(Course.id == row.prerequisite_course_id)
            .first()
        )
        # TODO: Remove this level-based fallback once every student has a complete
        # transcript. Until then, lower-level courses are treated as passed.
        if (
            not has_transcript_records
            and prerequisite is not None
            and prerequisite.level is not None
            and student.level is not None
            and prerequisite.level < student.level
        ):
            continue

        missing_codes.append(
            prerequisite.course_code
            if prerequisite is not None
            else str(row.prerequisite_course_id)
        )
    return missing_codes


def _student_enrollment_status(
    db: Session,
    student: Student,
    user: User,
    offering: CourseOffering,
    course: Course,
    course_level: int | None,
    capacity: int,
    current_enrolled_count: int,
) -> dict:
    existing_registration = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.student_id == student.id,
            CourseRegistration.course_offering_id == offering.id,
        )
        .order_by(CourseRegistration.id.asc())
        .first()
    )
    if (
        existing_registration is not None
        and existing_registration.status
        in registration_rules.ACTIVE_REGISTRATION_STATUSES
    ):
        return {
            "status": "already_enrolled",
            "is_enrolled": True,
            "is_selectable": False,
            "reason": "Already enrolled in this course",
        }
    if (
        existing_registration is not None
        and existing_registration.status != "dropped"
    ):
        return {
            "status": "not_eligible",
            "is_enrolled": False,
            "is_selectable": False,
            "reason": "A registration record already exists for this course offering",
        }
    if not user.is_active:
        return {
            "status": "not_eligible",
            "is_enrolled": False,
            "is_selectable": False,
            "reason": "Student account is inactive",
        }
    if current_enrolled_count >= capacity:
        return {
            "status": "not_eligible",
            "is_enrolled": False,
            "is_selectable": False,
            "reason": "Course is full",
        }
    if (
        course_level is not None
        and student.level is not None
        and student.level < course_level
    ):
        return {
            "status": "not_eligible",
            "is_enrolled": False,
            "is_selectable": False,
            "reason": "Student level is lower than course level",
        }
    if registration_rules.has_passed_course(db, student.id, course.id):
        return {
            "status": "not_eligible",
            "is_enrolled": False,
            "is_selectable": False,
            "reason": "Student already passed this course",
        }

    missing_prerequisites = _missing_prerequisite_codes(db, student, course)
    if missing_prerequisites:
        return {
            "status": "not_eligible",
            "is_enrolled": False,
            "is_selectable": False,
            "reason": (
                "Missing prerequisites: "
                + ", ".join(missing_prerequisites)
            ),
        }
    if student.cgpa is not None and student.cgpa < 2.5:
        return {
            "status": "at_risk",
            "is_enrolled": False,
            "is_selectable": True,
            "reason": "Eligible for enrollment; student is academically at risk",
        }
    return {
        "status": "eligible",
        "is_enrolled": False,
        "is_selectable": True,
        "reason": "Eligible for enrollment",
    }


def _course_enrollment_students_payload(
    db: Session,
    offering: CourseOffering,
    course: Course,
    semester: Semester | None,
) -> dict:
    course_payload = _course_payload(db, offering, course, semester)
    students = db.query(Student).order_by(Student.id.asc()).all()
    result = []
    for student in students:
        user = (
            db.query(User)
            .filter(User.id == student.user_id, User.role == "student")
            .first()
        )
        if user is None:
            continue
        eligibility = _student_enrollment_status(
            db,
            student,
            user,
            offering,
            course,
            course_payload["level"],
            course_payload["capacity"],
            course_payload["current_enrolled_count"],
        )
        result.append(
            {
                "student_id": student.id,
                "user_id": user.id,
                "university_id": user.university_id,
                "full_name": user.full_name,
                "email": user.email,
                "department_id": student.department_id,
                "department_name": _get_department_name(
                    db,
                    student.department_id,
                ),
                "level": student.level,
                "cgpa": student.cgpa,
                **eligibility,
            }
        )

    return {
        "course": course_payload,
        "students": sorted(
            result,
            key=lambda item: (
                str(item["full_name"]).lower(),
                str(item["university_id"]),
            ),
        ),
    }


def _student_payload(
    db: Session,
    student: Student,
    relationship_type: str,
) -> dict | None:
    user = db.query(User).filter(User.id == student.user_id).first()
    if user is None or user.role != "student":
        return None
    metrics = recalculate_student_academic_metrics(db, student)
    return {
        "student_id": student.id,
        "user_id": user.id,
        "university_id": user.university_id,
        "full_name": user.full_name,
        "email": user.email,
        "department_id": student.department_id,
        "department_name": _get_department_name(db, student.department_id),
        "level": student.level,
        "cgpa": metrics["cgpa"],
        "passed_credit_hours": metrics["passed_credit_hours"],
        "completed_courses_count": metrics["completed_courses_count"],
        "has_gpa_data": metrics["has_gpa_data"],
        "risk_status": metrics["risk_status"],
        "status": "active" if user.is_active else "inactive",
        "relationship_type": relationship_type,
    }


def _course_registration_students_payload(
    db: Session,
    offering: CourseOffering,
    course: Course,
    semester: Semester | None,
) -> dict:
    registrations = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.course_offering_id == offering.id,
            CourseRegistration.status.in_(ROSTER_REGISTRATION_STATUSES),
        )
        .order_by(CourseRegistration.id.asc())
        .all()
    )
    students = []
    for registration in registrations:
        student = (
            db.query(Student)
            .filter(Student.id == registration.student_id)
            .first()
        )
        if student is None:
            continue
        payload = _student_payload(db, student, "course_student")
        if payload is None:
            continue
        students.append(
            {
                **payload,
                "registration_id": registration.id,
                "registration_status": registration.status,
                "registered_at": registration.registered_at,
                "final_grade": registration.final_grade,
                "is_passed": registration.is_passed,
            }
        )

    return {
        "course": _course_payload(db, offering, course, semester),
        "students": sorted(
            students,
            key=lambda item: (
                str(item["full_name"]).casefold(),
                str(item["university_id"]),
            ),
        ),
    }


@router.get("/me")
def get_faculty_profile(
    current_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    instructor = _get_instructor(db, current_user)
    assigned_courses_count = (
        db.query(CourseInstructor.course_offering_id)
        .filter(CourseInstructor.instructor_id == instructor.id)
        .distinct()
        .count()
    )
    return {
        "instructor_id": instructor.id,
        "user_id": current_user.id,
        "university_id": current_user.university_id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "faculty_id": instructor.faculty_id,
        "faculty_name": _get_faculty_name(db, instructor.faculty_id),
        "department_id": instructor.department_id,
        "department_name": _get_department_name(db, instructor.department_id),
        "academic_position": "Faculty Member",
        "specialization": instructor.specialization,
        "office_location": instructor.office_location,
        "phone": instructor.phone,
        "status": "active" if current_user.is_active else "inactive",
        "availability": (
            "full_load" if assigned_courses_count >= 3 else "available"
        ),
    }


@router.get("/my-students")
def get_faculty_students(
    current_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    instructor = _get_instructor(db, current_user)
    related_students: dict[int, tuple[Student, str]] = {}

    advisor_students = (
        db.query(Student)
        .filter(Student.advisor_instructor_id == instructor.id)
        .all()
    )
    for student in advisor_students:
        related_students[student.id] = (student, "advisor")

    assignment_rows = (
        db.query(CourseInstructor)
        .filter(CourseInstructor.instructor_id == instructor.id)
        .all()
    )
    offering_ids = {
        row.course_offering_id
        for row in assignment_rows
        if row.course_offering_id is not None
    }
    if offering_ids:
        registrations = (
            db.query(CourseRegistration)
            .filter(
                CourseRegistration.course_offering_id.in_(offering_ids),
                CourseRegistration.status.in_(
                    registration_rules.ACTIVE_REGISTRATION_STATUSES
                ),
            )
            .all()
        )
        registered_student_ids = {row.student_id for row in registrations}
        if registered_student_ids:
            course_students = (
                db.query(Student)
                .filter(Student.id.in_(registered_student_ids))
                .all()
            )
            for student in course_students:
                related_students.setdefault(
                    student.id,
                    (student, "course_student"),
                )

    result = []
    for student, relationship_type in related_students.values():
        payload = _student_payload(db, student, relationship_type)
        if payload is not None:
            result.append(payload)

    return sorted(
        result,
        key=lambda item: (
            str(item.get("full_name") or "").lower(),
            str(item.get("university_id") or ""),
        ),
    )


@router.get("/my-courses")
def get_faculty_courses(
    current_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    instructor = _get_instructor(db, current_user)
    assignments = (
        db.query(CourseInstructor)
        .filter(CourseInstructor.instructor_id == instructor.id)
        .order_by(CourseInstructor.id.asc())
        .all()
    )

    result = []
    seen_offering_ids: set[int] = set()
    for assignment in assignments:
        if assignment.course_offering_id in seen_offering_ids:
            continue
        seen_offering_ids.add(assignment.course_offering_id)
        offering = (
            db.query(CourseOffering)
            .filter(CourseOffering.id == assignment.course_offering_id)
            .first()
        )
        if offering is None:
            continue
        course = db.query(Course).filter(Course.id == offering.course_id).first()
        if course is None:
            continue
        semester = (
            db.query(Semester)
            .filter(Semester.id == offering.semester_id)
            .first()
        )
        semester_number = _semester_number(semester, offering.semester_id)
        enrolled_students_count = _active_registration_count(db, offering.id)

        result.append(
            {
                "course_instructor_id": assignment.id,
                "course_offering_id": offering.id,
                "course_id": course.id,
                "course_code": course.course_code,
                "course_title": course.title,
                "credit_hours": course.credit_hours,
                "semester_id": offering.semester_id,
                "semester_name": semester.name if semester is not None else None,
                "academic_year": _academic_year(
                    semester.start_date if semester is not None else None
                ),
                "term": _term_name(semester_number),
                "level": _course_level(course, semester_number),
                "department_id": course.department_id,
                "department_name": _get_department_name(db, course.department_id),
                "status": offering.status,
                "capacity": _offering_capacity(db, offering.id),
                "enrolled_students_count": enrolled_students_count,
            }
        )

    return sorted(
        result,
        key=lambda item: (
            int(item["semester_id"]),
            str(item["course_code"]).casefold(),
        ),
    )


@router.get("/course-offerings/{course_offering_id}")
def get_faculty_course_offering(
    course_offering_id: int,
    current_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    instructor = _get_instructor(db, current_user)
    offering, course, semester = _get_assigned_offering(
        db,
        instructor.id,
        course_offering_id,
    )
    return _course_payload(db, offering, course, semester)


@router.get("/course-offerings/{course_offering_id}/students")
def get_course_offering_enrollment_students(
    course_offering_id: int,
    current_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
    include_available: bool = False,
):
    instructor = _get_instructor(db, current_user)
    offering, course, semester = _get_assigned_offering(
        db,
        instructor.id,
        course_offering_id,
    )
    if include_available:
        return _course_enrollment_students_payload(
            db,
            offering,
            course,
            semester,
        )
    return _course_registration_students_payload(
        db,
        offering,
        course,
        semester,
    )


@router.get("/course-offerings/{course_offering_id}/available-students")
def get_course_offering_available_students(
    course_offering_id: int,
    current_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    instructor = _get_instructor(db, current_user)
    offering, course, semester = _get_assigned_offering(
        db,
        instructor.id,
        course_offering_id,
    )
    return _course_enrollment_students_payload(
        db,
        offering,
        course,
        semester,
    )


@router.get("/course-offerings/{course_offering_id}/registrations")
def get_course_offering_registrations(
    course_offering_id: int,
    current_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    instructor = _get_instructor(db, current_user)
    offering, course, semester = _get_assigned_offering(
        db,
        instructor.id,
        course_offering_id,
    )
    return _course_registration_students_payload(
        db,
        offering,
        course,
        semester,
    )


@router.post("/course-offerings/{course_offering_id}/enroll-students")
def enroll_students_in_course_offering(
    course_offering_id: int,
    body: EnrollStudentsRequest,
    current_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    instructor = _get_instructor(db, current_user)
    offering, course, semester = _get_assigned_offering(
        db,
        instructor.id,
        course_offering_id,
    )
    course_payload = _course_payload(db, offering, course, semester)
    student_ids = list(dict.fromkeys(body.student_ids))

    if course_payload["current_enrolled_count"] + len(student_ids) > course_payload["capacity"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected students exceed the remaining course capacity",
        )

    students_to_enroll: list[Student] = []
    for student_id in student_ids:
        student = db.query(Student).filter(Student.id == student_id).first()
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {student_id} not found",
            )
        user = (
            db.query(User)
            .filter(User.id == student.user_id, User.role == "student")
            .first()
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student user for {student_id} not found",
            )
        eligibility = _student_enrollment_status(
            db,
            student,
            user,
            offering,
            course,
            course_payload["level"],
            course_payload["capacity"],
            course_payload["current_enrolled_count"],
        )
        if not eligibility["is_selectable"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{user.full_name}: {eligibility['reason']}",
            )
        students_to_enroll.append(student)

    for student in students_to_enroll:
        existing_registration = (
            db.query(CourseRegistration)
            .filter(
                CourseRegistration.student_id == student.id,
                CourseRegistration.course_offering_id == offering.id,
            )
            .order_by(CourseRegistration.id.asc())
            .first()
        )
        if (
            existing_registration is not None
            and existing_registration.status == "dropped"
        ):
            existing_registration.status = "enrolled"
            existing_registration.added_by_user_id = current_user.id
            existing_registration.registered_at = datetime.now(timezone.utc)
            existing_registration.final_grade = None
            existing_registration.is_passed = None
            existing_registration.completed_at = None
        elif existing_registration is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Student {student.id} already has a registration "
                    "for this course offering"
                ),
            )
        else:
            db.add(
                CourseRegistration(
                    student_id=student.id,
                    course_offering_id=offering.id,
                    status="enrolled",
                    added_by_user_id=current_user.id,
                    registered_at=datetime.now(timezone.utc),
                )
            )

    db.commit()
    current_enrolled_count = _active_registration_count(db, offering.id)
    return {
        "message": "Students enrolled successfully",
        "course_offering_id": offering.id,
        "enrolled_student_ids": student_ids,
        "current_enrolled_count": current_enrolled_count,
        "remaining_seats": max(
            0,
            course_payload["capacity"] - current_enrolled_count,
        ),
    }
