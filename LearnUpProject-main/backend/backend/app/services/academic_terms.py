"""Faculty catalog term indexing (matches ``FAC-L{level}S{sem}-C{slot}`` course codes)."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import DefaultDict

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.course_offering import CourseOffering
from app.models.course_registration import CourseRegistration
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.user import User
from app.services import registration_rules

CODE_RE = re.compile(r"^([A-Z]+)-L(\d)S(\d)-C(\d)$")


def term_index(level: int, semester: int) -> int:
    return (level - 1) * 2 + (semester - 1)


def parse_catalog_course(course: Course) -> tuple[str, int, int, int] | None:
    m = CODE_RE.match(course.course_code or "")
    if not m:
        return None
    return m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))


def build_faculty_term_course_map(db: Session) -> dict[tuple[str, int], list[Course]]:
    by_key: DefaultDict[tuple[str, int], list[Course]] = defaultdict(list)
    for c in db.query(Course).all():
        parsed = parse_catalog_course(c)
        if not parsed:
            continue
        fac, level, sem, _slot = parsed
        ti = term_index(level, sem)
        by_key[(fac, ti)].append(c)
    for key in by_key:
        by_key[key].sort(key=lambda x: x.course_code)
    return dict(by_key)


def faculty_code_for_student(db: Session, student: Student) -> str:
    if student.faculty_id is None:
        raise ValueError("Student has no faculty_id")
    fac = db.query(Faculty).filter(Faculty.id == student.faculty_id).first()
    if fac is None:
        raise ValueError("Faculty not found for student")
    return str(fac.code)


def get_primary_offering(db: Session, course_id: int) -> CourseOffering | None:
    return (
        db.query(CourseOffering)
        .filter(CourseOffering.course_id == course_id)
        .order_by(CourseOffering.id.asc())
        .first()
    )


def recompute_passed_credit_hours(db: Session, student: Student, faculty_code: str) -> None:
    catalog = build_faculty_term_course_map(db)
    total = 0
    for (fac, _ti), lst in catalog.items():
        if fac != faculty_code:
            continue
        for c in lst:
            if registration_rules.has_cleared_course(db, student.id, c.id):
                total += int(c.credit_hours or 0)
    student.passed_credit_hours = total


def complete_term_for_student(
    db: Session,
    student: Student,
    term_index: int,
    acting_admin_user_id: int,
) -> dict:
    """Mark all six catalog courses in ``term_index`` as passed; enroll next term if any."""
    if term_index < 0 or term_index > 7:
        raise ValueError("term_index must be between 0 and 7")

    faculty_code = faculty_code_for_student(db, student)
    catalog = build_faculty_term_course_map(db)

    term_courses = catalog.get((faculty_code, term_index))
    if not term_courses or len(term_courses) != 6:
        raise ValueError(
            f"Term {term_index} for faculty {faculty_code} does not have exactly 6 catalog courses"
        )

    for prev_t in range(term_index):
        prev_list = catalog.get((faculty_code, prev_t))
        if not prev_list or len(prev_list) != 6:
            raise ValueError(f"Previous term {prev_t} is incomplete in the catalog")
        for c in prev_list:
            if not registration_rules.has_cleared_course(db, student.id, c.id):
                raise ValueError(
                    f"All courses in term {prev_t} must be completed before term {term_index}"
                )

    now = datetime.now(timezone.utc)
    marked = 0
    for c in term_courses:
        offering = get_primary_offering(db, c.id)
        if offering is None:
            raise ValueError(f"No course offering for course_id={c.id}")

        reg = (
            db.query(CourseRegistration)
            .filter(
                CourseRegistration.student_id == student.id,
                CourseRegistration.course_offering_id == offering.id,
            )
            .first()
        )
        if reg is None:
            reg = CourseRegistration(
                student_id=student.id,
                course_offering_id=offering.id,
                status="completed",
                added_by_user_id=acting_admin_user_id,
                final_grade="A",
                is_passed=True,
                completed_at=now,
            )
            db.add(reg)
        else:
            reg.status = "completed"
            reg.final_grade = "A"
            reg.is_passed = True
            reg.completed_at = now
            reg.added_by_user_id = acting_admin_user_id
        marked += 1

    next_enrolled = 0
    if term_index < 7:
        next_list = catalog.get((faculty_code, term_index + 1))
        if next_list and len(next_list) == 6:
            for c in next_list:
                offering = get_primary_offering(db, c.id)
                if offering is None:
                    continue
                existing = (
                    db.query(CourseRegistration)
                    .filter(
                        CourseRegistration.student_id == student.id,
                        CourseRegistration.course_offering_id == offering.id,
                    )
                    .first()
                )
                if existing is not None:
                    if registration_rules.has_cleared_course(db, student.id, c.id):
                        continue
                    if existing.status == "registered":
                        continue
                    if existing.status == "dropped":
                        existing.status = "registered"
                        existing.final_grade = None
                        existing.is_passed = None
                        existing.completed_at = None
                        existing.added_by_user_id = acting_admin_user_id
                        next_enrolled += 1
                    continue

                db.add(
                    CourseRegistration(
                        student_id=student.id,
                        course_offering_id=offering.id,
                        status="registered",
                        added_by_user_id=acting_admin_user_id,
                        final_grade=None,
                        is_passed=None,
                        completed_at=None,
                    )
                )
                next_enrolled += 1

    recompute_passed_credit_hours(db, student, faculty_code)
    db.commit()
    db.refresh(student)

    return {
        "student_id": student.id,
        "faculty_code": faculty_code,
        "term_index": term_index,
        "courses_marked": marked,
        "next_term_registrations_created_or_reactivated": next_enrolled,
    }


def complete_term_for_all_students(
    db: Session,
    term_index: int,
    acting_admin_user_id: int,
) -> dict:
    """Complete one catalog term for every student and return summary stats."""
    if term_index < 0 or term_index > 7:
        raise ValueError("term_index must be between 0 and 7")

    students = (
        db.query(Student)
        .join(User, User.id == Student.user_id)
        .filter(User.role == "student")
        .all()
    )

    total = len(students)
    processed = 0
    failed = 0
    total_courses_marked = 0
    total_next_term_registrations = 0
    failures: list[dict] = []

    for student in students:
        try:
            result = complete_term_for_student(
                db,
                student,
                term_index,
                acting_admin_user_id=acting_admin_user_id,
            )
            processed += 1
            total_courses_marked += int(result["courses_marked"])
            total_next_term_registrations += int(
                result["next_term_registrations_created_or_reactivated"]
            )
        except ValueError as exc:
            db.rollback()
            failed += 1
            failures.append({"student_id": student.id, "detail": str(exc)})

    return {
        "term_index": term_index,
        "students_total": total,
        "students_processed": processed,
        "students_failed": failed,
        "courses_marked_total": total_courses_marked,
        "next_term_registrations_created_or_reactivated_total": total_next_term_registrations,
        "failures": failures,
    }
