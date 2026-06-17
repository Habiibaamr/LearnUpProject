"""
Seed realistic academic catalog data for the LearnUp demo.

This script does not delete users, admins, instructors, students, or auth data.
It runs in two explicit phases:
1. Cleanup dummy/high-semester academic rows only.
2. Seed Semester 1-8, 32 realistic CS courses, offerings, prerequisites, and
   instructor assignments when instructors exist.

Run from the backend folder:
    python scripts/seed_real_academic_data.py
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.academic_catalog import (  # noqa: E402
    COURSE_PREREQUISITES,
    MAX_DEMO_SEMESTERS,
    REALISTIC_COURSE_CATALOG,
    parse_semester_number,
)
from app.core.database import Base, SessionLocal, engine  # noqa: E402
import app.models  # noqa: E402, F401
from app.models.course import Course  # noqa: E402
from app.models.course_instructor import CourseInstructor  # noqa: E402
from app.models.course_offering import CourseOffering  # noqa: E402
from app.models.course_prerequisite import CoursePrerequisite  # noqa: E402
from app.models.course_registration import CourseRegistration  # noqa: E402
from app.models.department import Department  # noqa: E402
from app.models.faculty import Faculty  # noqa: E402
from app.models.instructor import Instructor  # noqa: E402
from app.models.lecture_group import LectureGroup  # noqa: E402
from app.models.lecture_registration import LectureRegistration  # noqa: E402
from app.models.section_group import SectionGroup  # noqa: E402
from app.models.section_registration import SectionRegistration  # noqa: E402
from app.models.semester import Semester  # noqa: E402


CATALOG_CODES = {course.code for course in REALISTIC_COURSE_CATALOG}
EXPECTED_COURSE_COUNT = len(REALISTIC_COURSE_CATALOG)


def _semester_dates(semester_number: int) -> tuple[date, date]:
    start = date(2025, 9, 1) + timedelta(days=(semester_number - 1) * 120)
    return start, start + timedelta(days=105)


def _is_dummy_course(course: Course) -> bool:
    title = (course.title or "").strip().lower()
    code = (course.course_code or "").strip().upper()
    return title.startswith("introduction to topic ") or (
        code.startswith("CSE") and code[3:].isdigit() and len(code) == 7
    )


def _delete_by_ids(session: Session, model: type, ids: set[int]) -> int:
    if not ids:
        return 0
    return (
        session.query(model)
        .filter(model.id.in_(ids))
        .delete(synchronize_session=False)
    )


def _delete_by_field_ids(session: Session, model: type, field, ids: set[int]) -> int:
    if not ids:
        return 0
    return (
        session.query(model)
        .filter(field.in_(ids))
        .delete(synchronize_session=False)
    )


def cleanup_dummy_academic_data(session: Session) -> dict[str, int]:
    """Remove only dummy/high-semester academic rows and their academic children."""
    dummy_course_ids = {
        course.id for course in session.query(Course).all() if _is_dummy_course(course)
    }
    high_semester_ids = {
        semester.id
        for semester in session.query(Semester).all()
        if (parse_semester_number(semester.name) or 0) > MAX_DEMO_SEMESTERS
    }
    dummy_offering_ids = {
        offering.id
        for offering in session.query(CourseOffering).all()
        if offering.course_id in dummy_course_ids or offering.semester_id in high_semester_ids
    }
    lecture_group_ids = {
        row.id
        for row in session.query(LectureGroup.id)
        .filter(LectureGroup.course_offering_id.in_(dummy_offering_ids or {-1}))
        .all()
    }
    section_group_ids = {
        row.id
        for row in session.query(SectionGroup.id)
        .filter(SectionGroup.course_offering_id.in_(dummy_offering_ids or {-1}))
        .all()
    }

    deleted = {
        "lecture_registrations": _delete_by_field_ids(
            session,
            LectureRegistration,
            LectureRegistration.lecture_group_id,
            lecture_group_ids,
        ),
        "section_registrations": _delete_by_field_ids(
            session,
            SectionRegistration,
            SectionRegistration.section_group_id,
            section_group_ids,
        ),
        "course_registrations": _delete_by_field_ids(
            session,
            CourseRegistration,
            CourseRegistration.course_offering_id,
            dummy_offering_ids,
        ),
        "course_instructors": _delete_by_field_ids(
            session,
            CourseInstructor,
            CourseInstructor.course_offering_id,
            dummy_offering_ids,
        ),
        "lecture_groups": _delete_by_ids(session, LectureGroup, lecture_group_ids),
        "section_groups": _delete_by_ids(session, SectionGroup, section_group_ids),
        "course_offerings": _delete_by_ids(session, CourseOffering, dummy_offering_ids),
        "course_prerequisites": (
            session.query(CoursePrerequisite)
            .filter(
                (CoursePrerequisite.course_id.in_(dummy_course_ids or {-1}))
                | (CoursePrerequisite.prerequisite_course_id.in_(dummy_course_ids or {-1}))
            )
            .delete(synchronize_session=False)
        ),
        "courses": _delete_by_ids(session, Course, dummy_course_ids),
        "semesters": _delete_by_ids(session, Semester, high_semester_ids),
    }
    return deleted


def _ensure_computer_science_org(session: Session) -> tuple[Faculty, Department]:
    faculty = (
        session.query(Faculty)
        .filter(Faculty.code.in_(["CS", "FCS"]))
        .order_by(Faculty.id.asc())
        .first()
        or session.query(Faculty).order_by(Faculty.id.asc()).first()
    )
    if faculty is None:
        faculty = Faculty(name="Faculty of Computer Science", code="CS")
        session.add(faculty)
        session.flush()
    else:
        faculty.name = "Faculty of Computer Science"
        faculty.code = "CS"

    department = (
        session.query(Department)
        .filter(Department.faculty_id == faculty.id, Department.code.in_(["CS", "CSE"]))
        .order_by(Department.id.asc())
        .first()
        or session.query(Department)
        .filter(Department.faculty_id == faculty.id)
        .order_by(Department.id.asc())
        .first()
        or session.query(Department).order_by(Department.id.asc()).first()
    )
    if department is None:
        department = Department(name="Computer Science", code="CS", faculty_id=faculty.id)
        session.add(department)
        session.flush()
    else:
        department.name = "Computer Science"
        department.code = "CS"
        department.faculty_id = faculty.id

    return faculty, department


def _seed_semesters(session: Session) -> tuple[dict[int, Semester], dict[str, int]]:
    semesters_by_number: dict[int, Semester] = {}
    for semester in session.query(Semester).order_by(Semester.id.asc()).all():
        semester_number = parse_semester_number(semester.name)
        if semester_number and 1 <= semester_number <= MAX_DEMO_SEMESTERS:
            semesters_by_number.setdefault(semester_number, semester)

    stats = {"created": 0, "updated": 0, "total": MAX_DEMO_SEMESTERS}
    for semester_number in range(1, MAX_DEMO_SEMESTERS + 1):
        semester = semesters_by_number.get(semester_number)
        start_date, end_date = _semester_dates(semester_number)
        if semester is None:
            semester = Semester(
                name=f"Semester {semester_number}",
                start_date=start_date,
                end_date=end_date,
                is_active=True,
            )
            session.add(semester)
            session.flush()
            semesters_by_number[semester_number] = semester
            stats["created"] += 1
        else:
            semester.name = f"Semester {semester_number}"
            semester.start_date = start_date
            semester.end_date = end_date
            semester.is_active = True
            stats["updated"] += 1

    return semesters_by_number, stats


def _seed_courses(
    session: Session,
    faculty_id: int,
    department_id: int,
) -> tuple[dict[str, Course], dict[str, int]]:
    courses_by_code = {
        course.course_code: course
        for course in session.query(Course)
        .filter(Course.course_code.in_(CATALOG_CODES))
        .all()
    }
    stats = {"created": 0, "updated": 0, "total": EXPECTED_COURSE_COUNT}

    for catalog_course in REALISTIC_COURSE_CATALOG:
        course = courses_by_code.get(catalog_course.code)
        description = (
            f"{catalog_course.title} for Semester {catalog_course.semester} "
            "in the Computer Science demo catalog."
        )
        if course is None:
            course = Course(
                course_code=catalog_course.code,
                title=catalog_course.title,
                credit_hours=catalog_course.credit_hours,
                faculty_id=faculty_id,
                department_id=department_id,
                level=catalog_course.level,
                description=description,
            )
            session.add(course)
            session.flush()
            courses_by_code[catalog_course.code] = course
            stats["created"] += 1
        else:
            course.title = catalog_course.title
            course.credit_hours = catalog_course.credit_hours
            course.faculty_id = faculty_id
            course.department_id = department_id
            course.level = catalog_course.level
            course.description = description
            stats["updated"] += 1

    return courses_by_code, stats


def _seed_prerequisites(session: Session, courses_by_code: dict[str, Course]) -> dict[str, int]:
    catalog_course_ids = {course.id for course in courses_by_code.values()}
    deleted = (
        session.query(CoursePrerequisite)
        .filter(CoursePrerequisite.course_id.in_(catalog_course_ids))
        .delete(synchronize_session=False)
    )
    created = 0
    for course_code, prerequisite_codes in COURSE_PREREQUISITES.items():
        course = courses_by_code.get(course_code)
        if course is None:
            continue
        for prerequisite_code in prerequisite_codes:
            prerequisite = courses_by_code.get(prerequisite_code)
            if prerequisite is None:
                continue
            session.add(
                CoursePrerequisite(
                    course_id=course.id,
                    prerequisite_course_id=prerequisite.id,
                )
            )
            created += 1

    return {"deleted_existing": deleted, "created": created, "total": created}


def _seed_offerings_and_assignments(
    session: Session,
    courses_by_code: dict[str, Course],
    semesters_by_number: dict[int, Semester],
) -> tuple[dict[str, CourseOffering], dict[str, int]]:
    instructor_ids = [row.id for row in session.query(Instructor.id).order_by(Instructor.id.asc()).all()]
    offerings_by_code: dict[str, CourseOffering] = {}
    stats = {
        "created": 0,
        "updated": 0,
        "total": EXPECTED_COURSE_COUNT,
        "instructor_assignments_created": 0,
        "instructor_assignments_total": 0,
    }

    for index, catalog_course in enumerate(REALISTIC_COURSE_CATALOG):
        course = courses_by_code[catalog_course.code]
        semester = semesters_by_number[catalog_course.semester]
        offering = (
            session.query(CourseOffering)
            .filter(CourseOffering.course_id == course.id)
            .order_by(CourseOffering.id.asc())
            .first()
        )
        coordinator_id = instructor_ids[index % len(instructor_ids)] if instructor_ids else None

        if offering is None:
            offering = CourseOffering(
                course_id=course.id,
                semester_id=semester.id,
                coordinator_instructor_id=coordinator_id,
                status="open",
            )
            session.add(offering)
            session.flush()
            stats["created"] += 1
        else:
            offering.semester_id = semester.id
            offering.coordinator_instructor_id = coordinator_id
            offering.status = "open"
            stats["updated"] += 1

        offerings_by_code[catalog_course.code] = offering

        if coordinator_id is not None:
            existing_assignment = (
                session.query(CourseInstructor)
                .filter(
                    CourseInstructor.course_offering_id == offering.id,
                    CourseInstructor.instructor_id == coordinator_id,
                )
                .first()
            )
            if existing_assignment is None:
                session.add(
                    CourseInstructor(
                        course_offering_id=offering.id,
                        instructor_id=coordinator_id,
                    )
                )
                stats["instructor_assignments_created"] += 1
            stats["instructor_assignments_total"] += 1

    return offerings_by_code, stats


def seed_real_academic_data(session: Session) -> dict[str, Any]:
    """Seed realistic catalog rows after cleanup has already run."""
    faculty, department = _ensure_computer_science_org(session)
    semesters_by_number, semester_stats = _seed_semesters(session)
    courses_by_code, course_stats = _seed_courses(session, faculty.id, department.id)
    prerequisite_stats = _seed_prerequisites(session, courses_by_code)
    offerings_by_code, offering_stats = _seed_offerings_and_assignments(
        session,
        courses_by_code,
        semesters_by_number,
    )

    session.flush()
    return {
        "semesters": semester_stats,
        "courses": course_stats,
        "prerequisites": prerequisite_stats,
        "offerings": offering_stats,
        "realistic_offering_count": len(offerings_by_code),
    }


def verify_real_academic_data(session: Session) -> dict[str, Any]:
    dummy_course_count = sum(1 for course in session.query(Course).all() if _is_dummy_course(course))
    high_semester_count = sum(
        1
        for semester in session.query(Semester).all()
        if (parse_semester_number(semester.name) or 0) > MAX_DEMO_SEMESTERS
    )
    realistic_offerings = (
        session.query(CourseOffering, Course, Semester)
        .join(Course, Course.id == CourseOffering.course_id)
        .join(Semester, Semester.id == CourseOffering.semester_id)
        .filter(Course.course_code.in_(CATALOG_CODES))
        .all()
    )
    valid_realistic_offering_count = sum(
        1
        for _offering, _course, semester in realistic_offerings
        if 1 <= (parse_semester_number(semester.name) or 0) <= MAX_DEMO_SEMESTERS
    )

    checks = {
        "realistic_offerings": valid_realistic_offering_count,
        "dummy_courses": dummy_course_count,
        "high_semesters": high_semester_count,
        "expected_offerings": EXPECTED_COURSE_COUNT,
    }
    checks["ok"] = (
        valid_realistic_offering_count == EXPECTED_COURSE_COUNT
        and dummy_course_count == 0
        and high_semester_count == 0
    )
    return checks


def print_summary(
    deleted: dict[str, int],
    seeded: dict[str, Any],
    verification: dict[str, Any],
    dry_run: bool,
) -> None:
    print("Cleanup complete: deleted dummy/high-semester academic rows")
    for key, value in deleted.items():
        print(f"  {key}: {value}")
    print("  users/admins/instructors/students: 0")
    print()

    print("Seed complete: realistic academic catalog")
    print(
        "  Created semesters count: "
        f"{seeded['semesters']['created']} "
        f"(updated {seeded['semesters']['updated']}, total {seeded['semesters']['total']})"
    )
    print(
        "  Created courses count: "
        f"{seeded['courses']['created']} "
        f"(updated {seeded['courses']['updated']}, total {seeded['courses']['total']})"
    )
    print(
        "  Created offerings count: "
        f"{seeded['offerings']['created']} "
        f"(updated {seeded['offerings']['updated']}, total {seeded['offerings']['total']})"
    )
    print(
        "  Created prerequisites count: "
        f"{seeded['prerequisites']['created']} "
        f"(replaced {seeded['prerequisites']['deleted_existing']} existing prerequisite rows)"
    )
    print(
        "  Created instructor assignments count: "
        f"{seeded['offerings']['instructor_assignments_created']} "
        f"(total assignable offerings {seeded['offerings']['instructor_assignments_total']})"
    )
    print()

    print("Verification")
    print(f"  /admin/course-offerings realistic offering count: {verification['realistic_offerings']}")
    print(f"  Introduction to Topic / CSE dummy course count: {verification['dummy_courses']}")
    print(f"  Semester above 8 count: {verification['high_semesters']}")
    print(f"  Expected realistic offerings: {verification['expected_offerings']}")
    print(f"  Result: {'PASS' if verification['ok'] else 'FAIL'}")
    print()
    print("Dry run: no data was changed." if dry_run else "Changes committed.")


def run(dry_run: bool = False) -> dict[str, Any]:
    if engine is None or SessionLocal is None:
        raise RuntimeError("Database is not configured. Set DATABASE_URL or NEON_URL.")

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        deleted = cleanup_dummy_academic_data(session)
        seeded = seed_real_academic_data(session)
        verification = verify_real_academic_data(session)

        if dry_run:
            session.rollback()
        elif verification["ok"]:
            session.commit()
        else:
            session.rollback()

        print_summary(deleted, seeded, verification, dry_run)

        if not verification["ok"]:
            raise RuntimeError("Academic catalog verification failed; transaction rolled back.")

        return {"deleted": deleted, "seeded": seeded, "verification": verification}
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
        help="Run cleanup, seed, and verification without committing changes.",
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
