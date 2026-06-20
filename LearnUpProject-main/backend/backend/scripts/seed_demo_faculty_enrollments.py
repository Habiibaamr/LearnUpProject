"""Safely add demo students and registrations for assigned faculty offerings.

This seed is intentionally additive:
- it never deletes users, students, instructors, courses, or offerings;
- it never replaces CourseInstructor assignments;
- it only creates CourseRegistration rows for missing student/offering pairs;
- it can be run repeatedly without creating duplicate pairs.

Run from the backend directory:
    python scripts/seed_demo_faculty_enrollments.py --dry-run
    python scripts/seed_demo_faculty_enrollments.py
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import bcrypt
from sqlalchemy import func
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.models  # noqa: E402, F401
from app.academic_catalog import parse_semester_number  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.course import Course  # noqa: E402
from app.models.course_instructor import CourseInstructor  # noqa: E402
from app.models.course_offering import CourseOffering  # noqa: E402
from app.models.course_registration import CourseRegistration  # noqa: E402
from app.models.department import Department  # noqa: E402
from app.models.instructor import Instructor  # noqa: E402
from app.models.semester import Semester  # noqa: E402
from app.models.student import Student  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.registration_rules import (  # noqa: E402
    ACTIVE_REGISTRATION_STATUSES,
)


ACTIVE_TARGET_PER_OFFERING = 3
DEMO_PASSWORD = "LearnUpDemo123!"
DEMO_STUDENTS = (
    {
        "full_name": "Nourhan Ahmed",
        "email": "nourhan.ahmed.demo@learnup.edu",
        "university_id": "DEMO-STU-001",
        "department": "Artificial Intelligence",
        "level": 1,
        "cgpa": 3.60,
    },
    {
        "full_name": "Salma Ibrahim",
        "email": "salma.ibrahim.demo@learnup.edu",
        "university_id": "DEMO-STU-002",
        "department": "Information System",
        "level": 2,
        "cgpa": 3.50,
    },
    {
        "full_name": "Ahmed Nabil",
        "email": "ahmed.nabil.demo@learnup.edu",
        "university_id": "DEMO-STU-003",
        "department": "Cyber Security",
        "level": 4,
        "cgpa": 2.80,
    },
    {
        "full_name": "Rana Mostafa",
        "email": "rana.mostafa.demo@learnup.edu",
        "university_id": "DEMO-STU-004",
        "department": "Computer Science",
        "level": 4,
        "cgpa": 3.20,
    },
    {
        "full_name": "Karim Samir",
        "email": "karim.samir.demo@learnup.edu",
        "university_id": "DEMO-STU-005",
        "department": "Computer Science",
        "level": 4,
        "cgpa": 3.35,
    },
    {
        "full_name": "Omar Hassan",
        "email": "omar.hassan.demo@learnup.edu",
        "university_id": "DEMO-STU-006",
        "department": "Artificial Intelligence",
        "level": 4,
        "cgpa": 3.05,
    },
)
DEMO_CGPAS = (3.20, 3.50, 2.80, 3.60, 3.35, 3.05)
COMPLETED_GRADES = (("A", True), ("B+", True), ("C", True), ("F", False))


def _course_level(
    course: Course,
    semester: Semester | None,
    semester_id: int,
) -> int:
    if course.level is not None:
        return max(1, min(4, int(course.level)))
    semester_number = parse_semester_number(
        semester.name if semester is not None else semester_id
    )
    if semester_number is None:
        return 1
    return max(1, min(4, ((semester_number - 1) // 2) + 1))


def _department_by_name(
    session: Session,
    name: str,
    fallback_department_id: int | None,
) -> Department | None:
    department = (
        session.query(Department)
        .filter(func.lower(Department.name) == name.casefold())
        .first()
    )
    if department is not None:
        return department
    if fallback_department_id is not None:
        department = (
            session.query(Department)
            .filter(Department.id == fallback_department_id)
            .first()
        )
        if department is not None:
            return department
    return session.query(Department).order_by(Department.id.asc()).first()


def _ensure_demo_student(
    session: Session,
    blueprint: dict[str, Any],
    faculty_id: int | None,
    fallback_department_id: int | None,
) -> tuple[Student, bool]:
    user = (
        session.query(User)
        .filter(
            (func.lower(User.email) == blueprint["email"].casefold())
            | (User.university_id == blueprint["university_id"])
        )
        .first()
    )
    created = False
    if user is None:
        password_hash = bcrypt.hashpw(
            DEMO_PASSWORD.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")
        user = User(
            university_id=blueprint["university_id"],
            full_name=blueprint["full_name"],
            email=blueprint["email"],
            password_hash=password_hash,
            role="student",
            is_active=True,
        )
        session.add(user)
        session.flush()
        created = True
    elif user.role != "student":
        raise RuntimeError(
            f"{blueprint['email']} exists but is not a student account"
        )
    else:
        user.is_active = True

    student = (
        session.query(Student)
        .filter(Student.user_id == user.id)
        .first()
    )
    department = _department_by_name(
        session,
        blueprint["department"],
        fallback_department_id,
    )
    if student is None:
        student = Student(
            user_id=user.id,
            faculty_id=faculty_id,
            department_id=department.id if department is not None else None,
            level=blueprint["level"],
            cgpa=blueprint["cgpa"],
            passed_credit_hours=0,
        )
        session.add(student)
        session.flush()
        created = True
    else:
        if student.faculty_id is None:
            student.faculty_id = faculty_id
        if student.department_id is None and department is not None:
            student.department_id = department.id
        if student.level is None or student.level < blueprint["level"]:
            student.level = blueprint["level"]
        if student.cgpa is None:
            student.cgpa = blueprint["cgpa"]

    return student, created


def _candidate_students(
    session: Session,
    course_level: int,
    excluded_student_ids: set[int],
) -> list[Student]:
    rows = (
        session.query(Student, User)
        .join(User, User.id == Student.user_id)
        .filter(User.role == "student", User.is_active.is_(True))
        .order_by(Student.id.asc())
        .all()
    )
    students = [
        student
        for student, _user in rows
        if student.id not in excluded_student_ids
        and (student.level is None or student.level >= course_level)
    ]
    return sorted(
        students,
        key=lambda student: (
            0 if student.level == course_level else 1,
            student.level or course_level,
            student.id,
        ),
    )


def _ensure_candidate_pool(
    session: Session,
    course: Course,
    course_level: int,
    excluded_student_ids: set[int],
    required_count: int,
    stats: dict[str, int],
) -> list[Student]:
    candidates = _candidate_students(
        session,
        course_level,
        excluded_student_ids,
    )
    if len(candidates) >= required_count:
        return candidates

    candidate_ids = {student.id for student in candidates}
    for blueprint in DEMO_STUDENTS:
        if blueprint["level"] < course_level:
            continue
        student, created = _ensure_demo_student(
            session,
            blueprint,
            course.faculty_id,
            course.department_id,
        )
        if created:
            stats["demo_students_created"] += 1
        if (
            student.id not in excluded_student_ids
            and student.id not in candidate_ids
        ):
            candidates.append(student)
            candidate_ids.add(student.id)
        if len(candidates) >= required_count:
            break

    return sorted(
        {student.id: student for student in candidates}.values(),
        key=lambda student: (
            0 if student.level == course_level else 1,
            student.level or course_level,
            student.id,
        ),
    )


def seed_demo_faculty_enrollments(session: Session) -> dict[str, int]:
    stats = {
        "assigned_offerings": 0,
        "demo_students_created": 0,
        "student_cgpas_filled": 0,
        "enrolled_registrations_created": 0,
        "completed_registrations_created": 0,
        "offerings_below_target": 0,
    }
    offering_ids = [
        row[0]
        for row in session.query(CourseInstructor.course_offering_id)
        .distinct()
        .order_by(CourseInstructor.course_offering_id.asc())
        .all()
        if row[0] is not None
    ]

    for offering_id in offering_ids:
        offering = (
            session.query(CourseOffering)
            .filter(CourseOffering.id == offering_id)
            .first()
        )
        if offering is None:
            continue
        course = (
            session.query(Course)
            .filter(Course.id == offering.course_id)
            .first()
        )
        if course is None:
            continue
        semester = (
            session.query(Semester)
            .filter(Semester.id == offering.semester_id)
            .first()
        )
        assignment = (
            session.query(CourseInstructor)
            .filter(CourseInstructor.course_offering_id == offering.id)
            .order_by(CourseInstructor.id.asc())
            .first()
        )
        instructor = (
            session.query(Instructor)
            .filter(Instructor.id == assignment.instructor_id)
            .first()
            if assignment is not None
            else None
        )
        stats["assigned_offerings"] += 1

        existing_registrations = (
            session.query(CourseRegistration)
            .filter(CourseRegistration.course_offering_id == offering.id)
            .all()
        )
        existing_student_ids = {
            registration.student_id for registration in existing_registrations
        }
        active_count = sum(
            1
            for registration in existing_registrations
            if registration.status in ACTIVE_REGISTRATION_STATUSES
        )
        active_needed = max(0, ACTIVE_TARGET_PER_OFFERING - active_count)
        has_completed = any(
            registration.status == "completed"
            for registration in existing_registrations
        )
        total_needed = active_needed + (0 if has_completed else 1)
        course_level = _course_level(course, semester, offering.semester_id)
        candidates = _ensure_candidate_pool(
            session,
            course,
            course_level,
            set(existing_student_ids),
            total_needed,
            stats,
        )
        now = datetime.now(timezone.utc)

        for index, student in enumerate(candidates[:active_needed]):
            if student.cgpa is None:
                student.cgpa = DEMO_CGPAS[
                    (offering.id + index) % len(DEMO_CGPAS)
                ]
                stats["student_cgpas_filled"] += 1
            session.add(
                CourseRegistration(
                    student_id=student.id,
                    course_offering_id=offering.id,
                    status="enrolled",
                    added_by_user_id=(
                        instructor.user_id if instructor is not None else None
                    ),
                    registered_at=now,
                )
            )
            stats["enrolled_registrations_created"] += 1

        remaining_candidates = candidates[active_needed:]
        if not has_completed and remaining_candidates:
            student = remaining_candidates[0]
            if student.cgpa is None:
                student.cgpa = DEMO_CGPAS[offering.id % len(DEMO_CGPAS)]
                stats["student_cgpas_filled"] += 1
            grade, is_passed = COMPLETED_GRADES[
                offering.id % len(COMPLETED_GRADES)
            ]
            session.add(
                CourseRegistration(
                    student_id=student.id,
                    course_offering_id=offering.id,
                    status="completed",
                    added_by_user_id=(
                        instructor.user_id if instructor is not None else None
                    ),
                    registered_at=now,
                    final_grade=grade,
                    is_passed=is_passed,
                    completed_at=now,
                )
            )
            stats["completed_registrations_created"] += 1

        if active_count + min(active_needed, len(candidates)) < ACTIVE_TARGET_PER_OFFERING:
            stats["offerings_below_target"] += 1

    session.flush()
    return stats


def run(dry_run: bool = False) -> dict[str, int]:
    if engine is None or SessionLocal is None:
        raise RuntimeError("Database is not configured. Set DATABASE_URL or NEON_URL.")

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        stats = seed_demo_faculty_enrollments(session)
        if dry_run:
            session.rollback()
        else:
            session.commit()

        print("Demo faculty enrollment seed")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print("  destructive changes: 0")
        print("Dry run: no data was changed." if dry_run else "Changes committed.")
        return stats
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate and validate changes, then roll the transaction back.",
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
