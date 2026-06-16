"""
Safely normalize LearnUp departments to the four demo departments.

This script does not delete users, admins, instructors, students, or auth data.
It upserts the four allowed department rows, remaps existing student,
instructor, and course department_id values to those rows, then removes extra
department rows.

Run from the backend folder:
    python scripts/seed_departments.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
import app.models  # noqa: E402, F401
from app.models.course import Course  # noqa: E402
from app.models.department import Department  # noqa: E402
from app.models.faculty import Faculty  # noqa: E402
from app.models.instructor import Instructor  # noqa: E402
from app.models.student import Student  # noqa: E402


ALLOWED_DEPARTMENTS = [
    (1, "Artificial Intelligence", "AI"),
    (2, "Information System", "IS"),
    (3, "Cyber Security", "CY"),
    (4, "Computer Science", "CS"),
]
ALLOWED_DEPARTMENT_IDS = {department_id for department_id, _name, _code in ALLOWED_DEPARTMENTS}


def _target_department_id(department_id: int | None) -> int | None:
    if department_id is None:
        return None

    if department_id in ALLOWED_DEPARTMENT_IDS:
        return department_id

    remainder = department_id % len(ALLOWED_DEPARTMENTS)
    return {0: 1, 1: 2, 2: 3, 3: 4}[remainder]


def _ensure_faculty(session: Session) -> Faculty:
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

    return faculty


def normalize_departments(session: Session) -> dict[str, int]:
    faculty = _ensure_faculty(session)
    stats = {
        "created_departments": 0,
        "updated_departments": 0,
        "remapped_students": 0,
        "remapped_instructors": 0,
        "remapped_courses": 0,
        "deleted_extra_departments": 0,
        "users_deleted": 0,
        "admins_deleted": 0,
        "instructors_deleted": 0,
        "students_deleted": 0,
    }

    for department_id, name, code in ALLOWED_DEPARTMENTS:
        department = session.query(Department).filter(Department.id == department_id).first()
        if department is None:
            department = Department(id=department_id, name=name, code=code, faculty_id=faculty.id)
            session.add(department)
            session.flush()
            stats["created_departments"] += 1
        else:
            department.name = name
            department.code = code
            department.faculty_id = faculty.id
            stats["updated_departments"] += 1

    for model, stat_key in [
        (Student, "remapped_students"),
        (Instructor, "remapped_instructors"),
        (Course, "remapped_courses"),
    ]:
        for row in session.query(model).all():
            target_department_id = _target_department_id(row.department_id)
            if target_department_id is not None and target_department_id != row.department_id:
                row.department_id = target_department_id
                stats[stat_key] += 1

    stats["deleted_extra_departments"] = (
        session.query(Department)
        .filter(~Department.id.in_(ALLOWED_DEPARTMENT_IDS))
        .delete(synchronize_session=False)
    )

    return stats


def main() -> None:
    if engine is None or SessionLocal is None:
        raise RuntimeError("Database is not configured. Set DATABASE_URL or NEON_URL.")

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        stats = normalize_departments(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print("Department normalization complete")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
