from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.course_offering import CourseOffering
from app.models.course_registration import CourseRegistration
from app.models.student import Student

GRADE_POINTS = {
    "A": 4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "D": 1.0,
    "F": 0.0,
}

LEVEL_TO_PREVIOUS_COURSE_CODES = {
    1: [],
    2: [
        "CS101",
        "CS102",
        "MA101",
        "HUM101",
    ],
    3: [
        "CS101",
        "CS102",
        "MA101",
        "HUM101",
        "CS103",
        "MA105",
        "ENG101",
        "PHY101",
    ],
    4: [
        "CS101",
        "CS102",
        "MA101",
        "HUM101",
        "CS103",
        "MA105",
        "ENG101",
        "PHY101",
        "CS201",
        "CS202",
        "MA201",
        "STAT201",
    ],
}

DEMO_LEVEL_GRADES = {
    "CS101": "A",
    "CS102": "B+",
    "MA101": "B",
    "HUM101": "A-",
    "CS103": "A-",
    "MA105": "B+",
    "ENG101": "A",
    "PHY101": "B",
}


def _normalise_grade(raw_value) -> str | None:
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    return text if text and text != "-" else None


def _is_passing_grade(grade: str | None) -> bool:
    return grade is not None and grade != "F"


def _get_course_for_offering(db: Session, offering_id: int) -> Course | None:
    offering = (
        db.query(CourseOffering)
        .filter(CourseOffering.id == offering_id)
        .first()
    )
    if offering is None:
        return None
    return (
        db.query(Course)
        .filter(Course.id == offering.course_id)
        .first()
    )


def _build_student_academic_summary(db: Session, student: Student) -> dict:
    completed_records = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.student_id == student.id,
            CourseRegistration.status == "completed",
        )
        .all()
    )

    total_points = 0.0
    total_hours = 0
    passed_hours = 0
    completed_count = 0

    for reg in completed_records:
        grade = _normalise_grade(reg.final_grade)
        if grade is None or grade not in GRADE_POINTS:
            continue

        course = _get_course_for_offering(db, reg.course_offering_id)
        if course is None or course.credit_hours is None:
            continue

        credit_hours = int(course.credit_hours)
        if credit_hours <= 0:
            continue

        completed_count += 1
        total_points += GRADE_POINTS[grade] * credit_hours
        total_hours += credit_hours
        if _is_passing_grade(grade):
            passed_hours += credit_hours

    if total_hours > 0:
        cgpa = round(total_points / total_hours, 4)
        has_gpa_data = True
    else:
        cgpa = None
        has_gpa_data = False

    if cgpa is not None and cgpa < 2.0:
        risk_status = "at_risk"
    elif cgpa is not None and cgpa < 2.5:
        risk_status = "needs_follow_up"
    elif cgpa is not None:
        risk_status = "good_standing"
    else:
        risk_status = "no_gpa_data"

    return {
        "cgpa": cgpa,
        "passed_credit_hours": passed_hours,
        "completed_courses_count": completed_count,
        "has_gpa_data": has_gpa_data,
        "risk_status": risk_status,
    }


def ensure_demo_student_history(db: Session, student: Student) -> None:
    if student.level is None or student.level < 2:
        return

    previous_codes = LEVEL_TO_PREVIOUS_COURSE_CODES.get(student.level, [])
    if not previous_codes:
        return

    for course_code in previous_codes:
        course = (
            db.query(Course)
            .filter(Course.course_code == course_code)
            .first()
        )
        if course is None:
            continue

        offering = (
            db.query(CourseOffering)
            .filter(CourseOffering.course_id == course.id)
            .order_by(CourseOffering.id.asc())
            .first()
        )
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
            continue

        grade = DEMO_LEVEL_GRADES.get(course_code)
        if grade is None:
            continue

        db.add(
            CourseRegistration(
                student_id=student.id,
                course_offering_id=offering.id,
                status="completed",
                final_grade=grade,
                is_passed=True,
                completed_at=None,
            )
        )


def recalculate_student_academic_metrics(db: Session, student: Student) -> dict:
    ensure_demo_student_history(db, student)
    summary = _build_student_academic_summary(db, student)
    student.cgpa = summary["cgpa"]
    student.passed_credit_hours = summary["passed_credit_hours"]
    return summary
