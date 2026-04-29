"""Shared course catalog board and enroll/drop by course id (student or staff acting for student)."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.course_offering import CourseOffering
from app.models.course_prerequisite import CoursePrerequisite
from app.models.course_registration import CourseRegistration
from app.models.student import Student
from app.services import registration_rules


def get_current_semester_id(db: Session) -> int:
    row = db.query(CourseOffering.semester_id).first()
    if row is not None:
        return int(row.semester_id)
    return 101


def get_or_create_offering_for_course(db: Session, course_id: int) -> CourseOffering:
    semester_id = get_current_semester_id(db)
    offering = (
        db.query(CourseOffering)
        .filter(
            CourseOffering.course_id == course_id,
            CourseOffering.semester_id == semester_id,
        )
        .first()
    )
    if offering is not None:
        return offering

    offering = CourseOffering(
        course_id=course_id,
        semester_id=semester_id,
        coordinator_instructor_id=None,
        status="open",
    )
    db.add(offering)
    db.commit()
    db.refresh(offering)
    return offering


def build_course_board(db: Session, student: Student) -> list[dict]:
    if student.faculty_id is None:
        return []

    courses = (
        db.query(Course)
        .filter(Course.faculty_id == student.faculty_id)
        .order_by(Course.level.asc(), Course.course_code.asc())
        .all()
    )
    if not courses:
        return []

    course_ids = [c.id for c in courses]

    prereq_rows = (
        db.query(CoursePrerequisite)
        .filter(CoursePrerequisite.course_id.in_(course_ids))
        .all()
    )
    prereq_map: dict[int, list[int]] = {}
    for row in prereq_rows:
        prereq_map.setdefault(row.course_id, []).append(row.prerequisite_course_id)

    registrations = (
        db.query(CourseRegistration, CourseOffering)
        .join(
            CourseOffering,
            CourseOffering.id == CourseRegistration.course_offering_id,
        )
        .filter(
            CourseRegistration.student_id == student.id,
            CourseOffering.course_id.in_(course_ids),
        )
        .all()
    )

    cleared_course_ids: set[int] = set()
    enrolled_offering_by_course_id: dict[int, int] = {}
    for reg, offering in registrations:
        if reg.status == "registered":
            enrolled_offering_by_course_id[offering.course_id] = offering.id
        if registration_rules.has_cleared_course(db, student.id, offering.course_id):
            cleared_course_ids.add(offering.course_id)

    result: list[dict] = []
    for course in courses:
        offering = get_or_create_offering_for_course(db, course.id)
        prereq_ids = prereq_map.get(course.id, [])
        missing_prereq_ids = [
            pid
            for pid in prereq_ids
            if not registration_rules.has_cleared_course(db, student.id, pid)
        ]

        if course.id in enrolled_offering_by_course_id:
            status_value = "enrolled"
            lock_reason = None
        elif course.id in cleared_course_ids:
            status_value = "passed"
            lock_reason = None
        elif student.level is not None and course.level is not None and course.level > student.level:
            status_value = "locked"
            lock_reason = "Level not reached"
        elif missing_prereq_ids:
            status_value = "locked"
            lock_reason = "Missing prerequisites"
        else:
            status_value = "available"
            lock_reason = None

        result.append(
            {
                "course_id": course.id,
                "course_offering_id": offering.id,
                "course_code": course.course_code,
                "title": course.title,
                "credit_hours": course.credit_hours,
                "level": course.level,
                "status": status_value,
                "lock_reason": lock_reason,
                "missing_prerequisite_ids": missing_prereq_ids,
                "can_add": status_value == "available",
                "can_drop": status_value == "enrolled",
            }
        )

    return result


def enroll_student_by_course_id(
    db: Session,
    student: Student,
    course_id: int,
    acting_user_id: int,
) -> dict:
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    offering = get_or_create_offering_for_course(db, course.id)

    existing = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.student_id == student.id,
            CourseRegistration.course_offering_id == offering.id,
            CourseRegistration.status == "registered",
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already registered for this course offering",
        )

    registration_rules.validate_course_registration_rules(db, student, offering.id)
    registration = CourseRegistration(
        student_id=student.id,
        course_offering_id=offering.id,
        status="registered",
        added_by_user_id=acting_user_id,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return {"message": "Course added successfully", "course_offering_id": offering.id}


def drop_student_by_course_id(db: Session, student: Student, course_id: int) -> dict:
    row = (
        db.query(CourseRegistration)
        .join(
            CourseOffering,
            CourseOffering.id == CourseRegistration.course_offering_id,
        )
        .filter(
            CourseRegistration.student_id == student.id,
            CourseOffering.course_id == course_id,
            CourseRegistration.status == "registered",
        )
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active registration not found for this course",
        )

    row.status = "dropped"
    db.commit()
    db.refresh(row)
    return {
        "message": "Course dropped successfully",
        "course_offering_id": row.course_offering_id,
    }
