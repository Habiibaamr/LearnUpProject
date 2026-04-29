"""
Seed Learnup_db with coherent dummy data. Run from the backend folder:
    python app/seed.py

Development note: `Base.metadata.create_all()` does not add columns to existing tables.
This script drops and recreates `course_registrations` and `course_prerequisites` so
their schema matches the models, then reseeds all data (full wipe via clear_all).
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

        base = date(2024, 1, 1)
        for i in range(1, 101):
            start = base + timedelta(days=(i - 1) * 30)
            end = start + timedelta(days=120)
            session.add(
                Semester(
                    name=f"Semester {i}",
                    start_date=start,
                    end_date=end,
                    is_active=(i % 10 != 0),
                )
            )
        session.commit()

        for i in range(1, 101):
            fid = ((i - 1) % 100) + 1
            did = ((i - 1) % 100) + 1
            session.add(
                Course(
                    course_code=f"CSE{i:04d}",
                    title=f"Introduction to Topic {i}",
                    credit_hours=((i - 1) % 4) + 2,
                    faculty_id=fid,
                    department_id=did,
                    level=((i - 1) % 4) + 1,
                    description=f"Course description for item {i}.",
                )
            )
        session.commit()

        for i in range(1, 101):
            prerequisite_course_id = i - 1 if i > 1 else 99
            session.add(
                CoursePrerequisite(
                    course_id=i,
                    prerequisite_course_id=prerequisite_course_id,
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

        for i in range(1, 101):
            coord = ((i - 1) % 30) + 1
            session.add(
                CourseOffering(
                    course_id=i,
                    semester_id=i,
                    coordinator_instructor_id=coord,
                    status="open",
                )
            )
        session.commit()

        for i in range(1, 101):
            inst_id = ((i - 1) % 30) + 1
            session.add(
                CourseInstructor(
                    course_offering_id=i,
                    instructor_id=inst_id,
                )
            )
        session.commit()

        for i in range(1, 101):
            inst_id = ((i - 1) % 30) + 1
            session.add(
                LectureGroup(
                    course_offering_id=i,
                    group_code=f"LEC-{i:03d}",
                    instructor_id=inst_id,
                    day_of_week=DAYS[(i - 1) % len(DAYS)],
                    start_time=time(9 + (i % 3), (i * 5) % 60),
                    end_time=time(10 + (i % 3), (i * 7) % 60),
                    room=f"Hall {100 + (i % 50)}",
                    capacity=100,
                )
            )
        session.commit()

        for i in range(1, 101):
            inst_id = ((i - 1) % 30) + 1
            session.add(
                SectionGroup(
                    course_offering_id=i,
                    group_code=f"SEC-{i:03d}",
                    instructor_id=inst_id,
                    day_of_week=DAYS[(i + 1) % len(DAYS)],
                    start_time=time(11 + (i % 2), (i * 3) % 60),
                    end_time=time(12 + (i % 2), (i * 11) % 60),
                    room=f"Lab {200 + (i % 40)}",
                    capacity=30,
                )
            )
        session.commit()

        now_utc = datetime.now(timezone.utc)
        for i in range(1, 101):
            added_by = 1 + ((i - 1) % 40)
            if i <= 40:
                session.add(
                    CourseRegistration(
                        student_id=i,
                        course_offering_id=i,
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
                        course_offering_id=i,
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
                        course_offering_id=i,
                        status="registered",
                        added_by_user_id=added_by,
                        final_grade=None,
                        is_passed=None,
                        completed_at=None,
                    )
                )
        session.commit()

        for i in range(1, 101):
            session.add(
                LectureRegistration(
                    student_id=i,
                    lecture_group_id=i,
                )
            )
        session.commit()

        for i in range(1, 101):
            session.add(
                SectionRegistration(
                    student_id=i,
                    section_group_id=i,
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

        print("Dummy data inserted successfully!")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
