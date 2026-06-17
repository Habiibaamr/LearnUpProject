from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_instructor
from app.models.course_instructor import CourseInstructor
from app.services import course_enrollment
from app.services import registration_rules
from app.services.academic_terms import parse_catalog_course, term_index
from app.services.grade_posting import get_window_status
from app.services.student_profile import get_or_create_student_row
from app.models.course import Course
from app.models.course_offering import CourseOffering
from app.models.course_registration import CourseRegistration
from app.models.instructor import Instructor
from app.models.student import Student
from app.models.user import User
from app.schemas.instructor import SubmitFinalGradeRequest

router = APIRouter(prefix="/instructor", tags=["instructor"])


def _get_student_by_university_id(db: Session, university_id: str) -> tuple[User, Student]:
    user = (
        db.query(User)
        .filter(User.university_id == university_id, User.role == "student")
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )
    try:
        student = get_or_create_student_row(db, user.id)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load student profile",
        ) from None
    return user, student


def _get_instructor_profile_or_404(db: Session, user: User) -> Instructor:
    instructor = db.query(Instructor).filter(Instructor.user_id == user.id).first()
    if instructor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor profile not found",
        )
    return instructor


def _require_assigned_to_offering(db: Session, instructor_id: int, course_offering_id: int) -> None:
    assignment = (
        db.query(CourseInstructor)
        .filter(
            CourseInstructor.instructor_id == instructor_id,
            CourseInstructor.course_offering_id == course_offering_id,
        )
        .first()
    )
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this course offering",
        )


def _ensure_grade_posting_open_for_offering(db: Session, course_offering: CourseOffering) -> None:
    window = get_window_status(db)
    if not window["is_open"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Final grades posting is locked by admin",
        )
    configured_term = window["term_index"]
    if configured_term is None:
        return
    course = db.query(Course).filter(Course.id == course_offering.course_id).first()
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found for this offering",
        )
    parsed = parse_catalog_course(course)
    if parsed is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course is not mapped to a catalog term; admin must handle this case",
        )
    _fac, level, semester, _slot = parsed
    offering_term = term_index(level, semester)
    if offering_term != configured_term:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Final grades window is open for term {configured_term}, not this offering term",
        )


@router.get("/students/{university_id}")
def get_student_by_university_id(
    university_id: str,
    _instructor: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    user, student = _get_student_by_university_id(db, university_id)
    return {
        "user_id": user.id,
        "student_id": student.id,
        "university_id": user.university_id,
        "full_name": user.full_name,
        "email": user.email,
        "photo_url": student.photo_url,
        "faculty_id": student.faculty_id,
        "department_id": student.department_id,
        "level": student.level,
        "cgpa": student.cgpa,
        "passed_credit_hours": student.passed_credit_hours,
        "phone": student.phone,
        "advisor_instructor_id": student.advisor_instructor_id,
    }


@router.get("/students/{university_id}/courses")
def list_student_courses(
    university_id: str,
    _instructor: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    _user, student = _get_student_by_university_id(db, university_id)
    registrations = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.student_id == student.id,
            CourseRegistration.status == "registered",
        )
        .all()
    )
    result = []
    for reg in registrations:
        offering = (
            db.query(CourseOffering)
            .filter(CourseOffering.id == reg.course_offering_id)
            .first()
        )
        if offering is None:
            continue
        course = db.query(Course).filter(Course.id == offering.course_id).first()
        if course is None:
            continue
        result.append(
            {
                "registration_id": reg.id,
                "student_id": student.id,
                "course_offering_id": reg.course_offering_id,
                "course_id": course.id,
                "course_code": course.course_code,
                "course_title": course.title,
                "credit_hours": course.credit_hours,
                "semester_id": offering.semester_id,
                "registration_status": reg.status,
                "registered_at": reg.registered_at,
            }
        )
    return result


@router.get("/students/{university_id}/course-board")
def get_student_course_board(
    university_id: str,
    _instructor: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    _user, student = _get_student_by_university_id(db, university_id)
    return {"courses": course_enrollment.build_course_board(db, student)}


@router.post("/students/{university_id}/add-course-by-course/{course_id}")
def add_course_for_student_by_course(
    university_id: str,
    course_id: int,
    instructor_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    _user, student = _get_student_by_university_id(db, university_id)
    return course_enrollment.enroll_student_by_course_id(
        db, student, course_id, acting_user_id=instructor_user.id
    )


@router.post("/students/{university_id}/drop-course-by-course/{course_id}")
def drop_course_for_student_by_course(
    university_id: str,
    course_id: int,
    _instructor: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    _user, student = _get_student_by_university_id(db, university_id)
    return course_enrollment.drop_student_by_course_id(db, student, course_id)


@router.post("/students/{university_id}/add-course/{course_offering_id}")
def add_course_for_student(
    university_id: str,
    course_offering_id: int,
    instructor_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    _, student = _get_student_by_university_id(db, university_id)

    existing = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.student_id == student.id,
            CourseRegistration.course_offering_id == course_offering_id,
            CourseRegistration.status == "registered",
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already registered for this course offering",
        )

    registration_rules.validate_course_registration_rules(
        db, student, course_offering_id
    )

    registration = CourseRegistration(
        student_id=student.id,
        course_offering_id=course_offering_id,
        status="registered",
        added_by_user_id=instructor_user.id,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)

    return {
        "message": "Course added successfully for student",
        "registration": {
            "id": registration.id,
            "student_id": registration.student_id,
            "course_offering_id": registration.course_offering_id,
            "status": registration.status,
            "added_by_user_id": registration.added_by_user_id,
            "registered_at": registration.registered_at,
        },
    }


@router.post("/students/{university_id}/drop-course/{course_offering_id}")
def drop_course_for_student(
    university_id: str,
    course_offering_id: int,
    _instructor: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    _, student = _get_student_by_university_id(db, university_id)

    registration = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.student_id == student.id,
            CourseRegistration.course_offering_id == course_offering_id,
            CourseRegistration.status == "registered",
        )
        .first()
    )
    if registration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active registration not found for this course offering",
        )

    registration.status = "dropped"
    db.commit()
    db.refresh(registration)

    return {
        "message": "Course dropped successfully for student",
        "registration": {
            "id": registration.id,
            "student_id": registration.student_id,
            "course_offering_id": registration.course_offering_id,
            "status": registration.status,
            "added_by_user_id": registration.added_by_user_id,
            "registered_at": registration.registered_at,
        },
    }


@router.get("/final-grades-window")
def get_final_grades_window_status(
    _instructor: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    return get_window_status(db)


@router.get("/my-offerings")
def list_my_offerings(
    instructor_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    instructor = _get_instructor_profile_or_404(db, instructor_user)
    rows = (
        db.query(CourseInstructor)
        .filter(CourseInstructor.instructor_id == instructor.id)
        .order_by(CourseInstructor.course_offering_id.asc())
        .all()
    )
    result = []
    for row in rows:
        offering = (
            db.query(CourseOffering)
            .filter(CourseOffering.id == row.course_offering_id)
            .first()
        )
        if offering is None:
            continue
        course = db.query(Course).filter(Course.id == offering.course_id).first()
        if course is None:
            continue
        result.append(
            {
                "course_offering_id": offering.id,
                "course_id": course.id,
                "course_code": course.course_code,
                "course_title": course.title,
                "credit_hours": course.credit_hours,
                "semester_id": offering.semester_id,
                "offering_status": offering.status,
            }
        )
    return result


@router.get("/my-offerings/{course_offering_id}/registrations")
def list_my_offering_registrations(
    course_offering_id: int,
    instructor_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    instructor = _get_instructor_profile_or_404(db, instructor_user)
    _require_assigned_to_offering(db, instructor.id, course_offering_id)
    regs = (
        db.query(CourseRegistration)
        .filter(CourseRegistration.course_offering_id == course_offering_id)
        .order_by(CourseRegistration.id.asc())
        .all()
    )
    result = []
    for reg in regs:
        student = db.query(Student).filter(Student.id == reg.student_id).first()
        if student is None:
            continue
        student_user = db.query(User).filter(User.id == student.user_id).first()
        if student_user is None:
            continue
        result.append(
            {
                "registration_id": reg.id,
                "student_id": student.id,
                "student_university_id": student_user.university_id,
                "student_full_name": student_user.full_name,
                "status": reg.status,
                "final_grade": reg.final_grade,
                "is_passed": reg.is_passed,
                "registered_at": reg.registered_at,
                "completed_at": reg.completed_at,
            }
        )
    return result


@router.post("/my-offerings/{course_offering_id}/registrations/{registration_id}/final-grade")
def submit_final_grade_for_registration(
    course_offering_id: int,
    registration_id: int,
    body: SubmitFinalGradeRequest,
    instructor_user: User = Depends(require_instructor),
    db: Session = Depends(get_db),
):
    instructor = _get_instructor_profile_or_404(db, instructor_user)
    _require_assigned_to_offering(db, instructor.id, course_offering_id)

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
    _ensure_grade_posting_open_for_offering(db, offering)

    reg = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.id == registration_id,
            CourseRegistration.course_offering_id == course_offering_id,
        )
        .first()
    )
    if reg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course registration not found",
        )

    reg.final_grade = body.final_grade.strip().upper()
    reg.is_passed = body.is_passed
    reg.status = "completed"
    reg.completed_at = datetime.now(timezone.utc)
    reg.added_by_user_id = instructor_user.id
    db.commit()
    db.refresh(reg)

    return {
        "message": "Final grade posted successfully",
        "registration": {
            "id": reg.id,
            "student_id": reg.student_id,
            "course_offering_id": reg.course_offering_id,
            "status": reg.status,
            "final_grade": reg.final_grade,
            "is_passed": reg.is_passed,
            "completed_at": reg.completed_at,
        },
    }
