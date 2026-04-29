from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.course_offering import CourseOffering
from app.models.course_prerequisite import CoursePrerequisite
from app.models.course_registration import CourseRegistration
from app.models.student import Student


def get_student_profile(db: Session, user_id: int) -> Optional[Student]:
    return db.query(Student).filter(Student.user_id == user_id).first()


def get_course_offering_with_course(
    db: Session, course_offering_id: int
) -> Tuple[Optional[CourseOffering], Optional[Course]]:
    offering = (
        db.query(CourseOffering)
        .filter(CourseOffering.id == course_offering_id)
        .first()
    )
    if offering is None:
        return None, None
    course = db.query(Course).filter(Course.id == offering.course_id).first()
    return offering, course


def has_cleared_course(db: Session, student_id: int, course_id: int) -> bool:
    """True when the student has successfully finished this course for prerequisite purposes.

    Counts explicit passes and completed registrations that are not recorded as failed.
    """
    return (
        db.query(CourseRegistration)
        .join(
            CourseOffering,
            CourseRegistration.course_offering_id == CourseOffering.id,
        )
        .filter(
            CourseRegistration.student_id == student_id,
            CourseOffering.course_id == course_id,
            or_(
                CourseRegistration.is_passed.is_(True),
                and_(
                    CourseRegistration.status == "completed",
                    or_(
                        CourseRegistration.is_passed.is_(None),
                        CourseRegistration.is_passed.is_(True),
                    ),
                ),
            ),
        )
        .first()
        is not None
    )


def has_passed_course(db: Session, student_id: int, course_id: int) -> bool:
    """Backward-compatible name: cleared / passed for registration rules."""
    return has_cleared_course(db, student_id, course_id)


def get_missing_prerequisites(db: Session, student_id: int, course_id: int) -> List[int]:
    prereq_rows = (
        db.query(CoursePrerequisite)
        .filter(CoursePrerequisite.course_id == course_id)
        .all()
    )
    missing: List[int] = []
    for row in prereq_rows:
        if not has_cleared_course(db, student_id, row.prerequisite_course_id):
            missing.append(row.prerequisite_course_id)
    return missing


def get_current_registered_credit_hours(db: Session, student_id: int) -> int:
    registrations = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.student_id == student_id,
            CourseRegistration.status == "registered",
        )
        .all()
    )
    total = 0
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
        total += course.credit_hours
    return total


def validate_course_registration_rules(
    db: Session,
    student: Student,
    course_offering_id: int,
) -> Tuple[CourseOffering, Course]:
    offering, course = get_course_offering_with_course(db, course_offering_id)
    if offering is None or course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course offering not found",
        )

    if (
        student.level is not None
        and course.level is not None
        and course.level > student.level
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Course level ({course.level}) is above your academic level ({student.level})"
            ),
        )

    if has_passed_course(db, student.id, course.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already passed this course and cannot register again",
        )

    missing = get_missing_prerequisites(db, student.id, course.id)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Missing passed prerequisites",
                "missing_prerequisite_course_ids": missing,
            },
        )

    max_credits = (
        21
        if student.cgpa is not None and student.cgpa >= 3.0
        else 18
    )
    current_hours = get_current_registered_credit_hours(db, student.id)
    if current_hours + course.credit_hours > max_credits:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Credit hour limit exceeded: current registered {current_hours} + "
                f"this course {course.credit_hours} exceeds maximum {max_credits} "
                f"for your CGPA band"
            ),
        )

    return offering, course
