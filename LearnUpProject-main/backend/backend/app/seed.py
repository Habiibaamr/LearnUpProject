"""
Seed Learnup_db with coherent demo data. Run from the backend folder:
    python app/seed.py

Development note: `Base.metadata.create_all()` does not add columns to existing tables.
This script drops and recreates `course_registrations` and `course_prerequisites` so
their schema matches the models, then reseeds all data (full wipe via clear_all).

WARNING: This script deletes users/admins/instructors/students. For an existing
demo database, prefer scripts/seed_real_academic_data.py.
"""
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import bcrypt
from sqlalchemy import text
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.academic_catalog import (  # noqa: E402
    COURSE_PREREQUISITES,
    MAX_DEMO_SEMESTERS,
    REALISTIC_COURSE_CATALOG,
)
import app.models  # noqa: E402, F401 — register ORM tables on Base.metadata
from app.models.admin import Admin  # noqa: E402
from app.models.chat_message import ChatMessage  # noqa: E402
from app.models.chat_session import ChatSession  # noqa: E402
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
from app.models.student import Student  # noqa: E402
from app.models.super_admin import SuperAdmin  # noqa: E402
from app.models.user import User  # noqa: E402

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Saturday"]


def _dev_reset_registration_tables() -> None:
    """Drop tables whose schema changed; create_all will recreate them."""
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS course_prerequisites CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS course_registrations CASCADE"))


def clear_all(session: Session) -> None:
    """Delete rows in dependency-safe order (children before parents)."""
    tables_order = [
        ChatMessage,
        ChatSession,
        SectionRegistration,
        LectureRegistration,
        CourseRegistration,
        SectionGroup,
        LectureGroup,
        CourseInstructor,
        CourseOffering,
        Course,
        Semester,
        Student,
        Instructor,
        SuperAdmin,
        Admin,
        Department,
        Faculty,
        User,
    ]
    for model in tables_order:
        session.query(model).delete()
    session.commit()


def seed() -> None:
    password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")

    _dev_reset_registration_tables()
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        clear_all(session)

        for i in range(1, 141):
            if i == 1:
                role = "super_admin"
            elif i <= 10:
                role = "admin"
            elif i <= 40:
                role = "instructor"
            else:
                role = "student"
            session.add(
                User(
                    university_id=f"U{i:06d}",
                    full_name=f"User {i} Full Name",
                    email=f"user{i}@learnup.edu",
                    password_hash=password_hash,
                    role=role,
                    is_active=True,
                )
            )
        session.commit()

        for i in range(1, 101):
            session.add(
                Faculty(
                    name=f"Faculty of Science {i}",
                    code=f"F{i:03d}",
                )
            )
        session.commit()

        for i in range(1, 101):
            faculty_id = ((i - 1) % 100) + 1
            session.add(
                Department(
                    name=f"Department {i}",
                    code=f"D{i:03d}",
                    faculty_id=faculty_id,
                )
            )
        session.commit()

        base = date(2025, 9, 1)
        for i in range(1, MAX_DEMO_SEMESTERS + 1):
            start = base + timedelta(days=(i - 1) * 120)
            end = start + timedelta(days=105)
            session.add(
                Semester(
                    name=f"Semester {i}",
                    start_date=start,
                    end_date=end,
                    is_active=True,
                )
            )
        session.commit()

        for catalog_course in REALISTIC_COURSE_CATALOG:
            session.add(
                Course(
                    course_code=catalog_course.code,
                    title=catalog_course.title,
                    credit_hours=catalog_course.credit_hours,
                    faculty_id=1,
                    department_id=1,
                    level=catalog_course.level,
                    description=(
                        f"{catalog_course.title} for Semester {catalog_course.semester} "
                        "in the Computer Science demo catalog."
                    ),
                )
            )
        session.commit()

        courses_by_code = {
            course.course_code: course
            for course in session.query(Course)
            .filter(Course.course_code.in_([course.code for course in REALISTIC_COURSE_CATALOG]))
            .all()
        }
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
        session.commit()

        session.add(
            SuperAdmin(
                user_id=1,
                position="Super Admin",
            )
        )
        for i in range(2, 11):
            session.add(Admin(user_id=i, position=f"Admin Position {i}"))
        session.commit()

        for i in range(1, 31):
            uid = 10 + i
            fid = ((i - 1) % 100) + 1
            did = ((i - 1) % 100) + 1
            session.add(
                Instructor(
                    user_id=uid,
                    faculty_id=fid,
                    department_id=did,
                    specialization=f"Specialization {i}",
                    office_location=f"Building {i % 20 + 1} Room {i % 50 + 100}",
                    phone=f"050{i % 1000000:06d}",
                )
            )
        session.commit()

        for i in range(1, 101):
            uid = 40 + i
            fid = ((i - 1) % 100) + 1
            did = ((i - 1) % 100) + 1
            adv = ((i - 1) % 30) + 1
            session.add(
                Student(
                    user_id=uid,
                    photo_url=f"https://example.edu/photos/u{uid}.jpg",
                    faculty_id=fid,
                    department_id=did,
                    level=((i - 1) % 4) + 1,
                    cgpa=round(2.0 + (i % 20) * 0.1, 2),
                    passed_credit_hours=((i - 1) * 3) % 140,
                    phone=f"055{i % 1000000:06d}",
                    advisor_instructor_id=adv,
                )
            )
        session.commit()

        semesters_by_number = {
            int(semester.name.split()[-1]): semester
            for semester in session.query(Semester).all()
            if semester.name.startswith("Semester ")
        }
        for index, catalog_course in enumerate(REALISTIC_COURSE_CATALOG):
            course = courses_by_code[catalog_course.code]
            semester = semesters_by_number[catalog_course.semester]
            coord = (index % 30) + 1
            session.add(
                CourseOffering(
                    course_id=course.id,
                    semester_id=semester.id,
                    coordinator_instructor_id=coord,
                    status="open",
                )
            )
        session.commit()

        offering_ids = [
            row.id for row in session.query(CourseOffering).order_by(CourseOffering.id.asc()).all()
        ]
        for index, offering_id in enumerate(offering_ids):
            inst_id = (index % 30) + 1
            session.add(
                CourseInstructor(
                    course_offering_id=offering_id,
                    instructor_id=inst_id,
                )
            )
        session.commit()

        for index, offering_id in enumerate(offering_ids, start=1):
            inst_id = ((index - 1) % 30) + 1
            session.add(
                LectureGroup(
                    course_offering_id=offering_id,
                    group_code=f"LEC-{index:03d}",
                    instructor_id=inst_id,
                    day_of_week=DAYS[(index - 1) % len(DAYS)],
                    start_time=time(9 + (index % 3), (index * 5) % 60),
                    end_time=time(10 + (index % 3), (index * 7) % 60),
                    room=f"Hall {100 + (index % 50)}",
                    capacity=100,
                )
            )
        session.commit()

        for index, offering_id in enumerate(offering_ids, start=1):
            inst_id = ((index - 1) % 30) + 1
            session.add(
                SectionGroup(
                    course_offering_id=offering_id,
                    group_code=f"SEC-{index:03d}",
                    instructor_id=inst_id,
                    day_of_week=DAYS[(index + 1) % len(DAYS)],
                    start_time=time(11 + (index % 2), (index * 3) % 60),
                    end_time=time(12 + (index % 2), (index * 11) % 60),
                    room=f"Lab {200 + (index % 40)}",
                    capacity=30,
                )
            )
        session.commit()

        now_utc = datetime.now(timezone.utc)
        offering_cycle = offering_ids or [1]
        for i in range(1, 101):
            added_by = 1 + ((i - 1) % 40)
            course_offering_id = offering_cycle[(i - 1) % len(offering_cycle)]
            if i <= 40:
                session.add(
                    CourseRegistration(
                        student_id=i,
                        course_offering_id=course_offering_id,
                        status="completed",
                        added_by_user_id=added_by,
                        final_grade="A"
                        if i % 3 == 0
                        else ("B+" if i % 3 == 1 else "C"),
                        is_passed=True,
                        completed_at=now_utc - timedelta(days=60 + i),
                    )
                )
            elif i <= 55:
                session.add(
                    CourseRegistration(
                        student_id=i,
                        course_offering_id=course_offering_id,
                        status="completed",
                        added_by_user_id=added_by,
                        final_grade="F",
                        is_passed=False,
                        completed_at=now_utc - timedelta(days=15 + i),
                    )
                )
            else:
                session.add(
                    CourseRegistration(
                        student_id=i,
                        course_offering_id=course_offering_id,
                        status="registered",
                        added_by_user_id=added_by,
                        final_grade=None,
                        is_passed=None,
                        completed_at=None,
                    )
                )
        session.commit()

        lecture_group_ids = [
            row.id for row in session.query(LectureGroup).order_by(LectureGroup.id.asc()).all()
        ]
        section_group_ids = [
            row.id for row in session.query(SectionGroup).order_by(SectionGroup.id.asc()).all()
        ]
        for i in range(1, 101):
            lecture_group_id = lecture_group_ids[(i - 1) % len(lecture_group_ids)]
            session.add(
                LectureRegistration(
                    student_id=i,
                    lecture_group_id=lecture_group_id,
                )
            )
        session.commit()

        for i in range(1, 101):
            section_group_id = section_group_ids[(i - 1) % len(section_group_ids)]
            session.add(
                SectionRegistration(
                    student_id=i,
                    section_group_id=section_group_id,
                )
            )
        session.commit()

        for i in range(1, 101):
            uid = ((i - 1) % 140) + 1
            session.add(ChatSession(user_id=uid))
        session.commit()

        for i in range(1, 101):
            sender = "user" if i % 2 == 1 else "assistant"
            session.add(
                ChatMessage(
                    session_id=i,
                    sender_type=sender,
                    message_text=f"Seed message {i} from {sender}.",
                )
            )
        session.commit()

        print("Realistic demo data inserted successfully!")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
