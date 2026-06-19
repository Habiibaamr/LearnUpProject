import unittest
from datetime import date

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.database import Base
from app.models.course import Course
from app.models.course_instructor import CourseInstructor
from app.models.course_offering import CourseOffering
from app.models.course_prerequisite import CoursePrerequisite
from app.models.course_registration import CourseRegistration
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.instructor import Instructor
from app.models.lecture_group import LectureGroup
from app.models.semester import Semester
from app.models.student import Student
from app.models.user import User
from app.routers.faculty import (
    EnrollStudentsRequest,
    enroll_students_in_course_offering,
    get_course_offering_enrollment_students,
    get_course_offering_registrations,
    get_faculty_courses,
    get_faculty_course_offering,
    get_faculty_profile,
    get_faculty_students,
)


class FacultyRouterTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        self.db = sessionmaker(bind=engine)()

        faculty = Faculty(id=1, name="Faculty of Computer Science", code="CS")
        department = Department(
            id=4,
            name="Computer Science",
            code="CS",
            faculty_id=faculty.id,
        )
        instructor_user = User(
            id=1,
            university_id="INS0001",
            full_name="Dr. Faculty Member",
            email="faculty@learnup.edu",
            password_hash="not-used",
            role="instructor",
            is_active=True,
        )
        advisor_student_user = User(
            id=2,
            university_id="STU0001",
            full_name="Advisor Student",
            email="advisor.student@learnup.edu",
            password_hash="not-used",
            role="student",
            is_active=True,
        )
        course_student_user = User(
            id=3,
            university_id="STU0002",
            full_name="Course Student",
            email="course.student@learnup.edu",
            password_hash="not-used",
            role="student",
            is_active=True,
        )
        unrelated_user = User(
            id=4,
            university_id="STU0003",
            full_name="Unrelated Student",
            email="unrelated.student@learnup.edu",
            password_hash="not-used",
            role="student",
            is_active=True,
        )
        eligible_user = User(
            id=5,
            university_id="STU0004",
            full_name="Eligible Student",
            email="eligible.student@learnup.edu",
            password_hash="not-used",
            role="student",
            is_active=True,
        )
        other_instructor_user = User(
            id=6,
            university_id="INS0002",
            full_name="Other Faculty Member",
            email="other.faculty@learnup.edu",
            password_hash="not-used",
            role="instructor",
            is_active=True,
        )
        self.db.add_all(
            [
                faculty,
                department,
                instructor_user,
                advisor_student_user,
                course_student_user,
                unrelated_user,
                eligible_user,
                other_instructor_user,
            ]
        )
        self.db.flush()

        instructor = Instructor(
            id=10,
            user_id=instructor_user.id,
            faculty_id=faculty.id,
            department_id=department.id,
            specialization="Software Engineering",
            office_location="B-204",
            phone="01000000000",
        )
        advisor_student = Student(
            id=20,
            user_id=advisor_student_user.id,
            faculty_id=faculty.id,
            department_id=department.id,
            level=2,
            cgpa=3.6,
            advisor_instructor_id=instructor.id,
        )
        course_student = Student(
            id=21,
            user_id=course_student_user.id,
            faculty_id=faculty.id,
            department_id=department.id,
            level=2,
            cgpa=3.1,
        )
        unrelated_student = Student(
            id=22,
            user_id=unrelated_user.id,
            faculty_id=faculty.id,
            department_id=department.id,
            level=1,
            cgpa=2.9,
        )
        eligible_student = Student(
            id=23,
            user_id=eligible_user.id,
            faculty_id=faculty.id,
            department_id=department.id,
            level=2,
            cgpa=3.3,
        )
        other_instructor = Instructor(
            id=11,
            user_id=other_instructor_user.id,
            faculty_id=faculty.id,
            department_id=department.id,
        )
        semester = Semester(
            id=3,
            name="Semester 3",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 1, 15),
            is_active=True,
        )
        course = Course(
            id=30,
            course_code="CS201",
            title="Data Structures",
            credit_hours=3,
            faculty_id=faculty.id,
            department_id=department.id,
            level=None,
        )
        prerequisite_course = Course(
            id=31,
            course_code="CS101",
            title="Programming Fundamentals",
            credit_hours=3,
            faculty_id=faculty.id,
            department_id=department.id,
            level=1,
        )
        offering = CourseOffering(
            id=40,
            course_id=course.id,
            semester_id=semester.id,
            status="open",
        )
        assignment = CourseInstructor(
            id=50,
            course_offering_id=offering.id,
            instructor_id=instructor.id,
        )
        self.db.add_all(
            [
                instructor,
                advisor_student,
                course_student,
                unrelated_student,
                eligible_student,
                other_instructor,
                semester,
                course,
                prerequisite_course,
                offering,
                assignment,
                CoursePrerequisite(
                    course_id=course.id,
                    prerequisite_course_id=prerequisite_course.id,
                ),
                CourseRegistration(
                    student_id=advisor_student.id,
                    course_offering_id=offering.id,
                    status="registered",
                ),
                CourseRegistration(
                    student_id=course_student.id,
                    course_offering_id=offering.id,
                    status="registered",
                ),
                LectureGroup(
                    course_offering_id=offering.id,
                    group_code="LEC-001",
                    instructor_id=instructor.id,
                    capacity=50,
                ),
            ]
        )
        self.db.commit()
        self.current_user = instructor_user
        self.other_instructor_user = other_instructor_user

    def tearDown(self):
        self.db.close()

    def test_profile_is_scoped_to_current_instructor(self):
        profile = get_faculty_profile(self.current_user, self.db)

        self.assertEqual(profile["instructor_id"], 10)
        self.assertEqual(profile["full_name"], "Dr. Faculty Member")
        self.assertEqual(profile["department_name"], "Computer Science")
        self.assertEqual(profile["faculty_name"], "Faculty of Computer Science")

    def test_students_merge_advisor_and_course_relationships(self):
        students = get_faculty_students(self.current_user, self.db)
        by_id = {student["university_id"]: student for student in students}

        self.assertEqual(set(by_id), {"STU0001", "STU0002"})
        self.assertEqual(by_id["STU0001"]["relationship_type"], "advisor")
        self.assertEqual(by_id["STU0002"]["relationship_type"], "course_student")

    def test_courses_are_assigned_and_level_falls_back_to_semester(self):
        courses = get_faculty_courses(self.current_user, self.db)

        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0]["course_code"], "CS201")
        self.assertEqual(courses[0]["level"], 2)
        self.assertEqual(courses[0]["enrolled_students_count"], 2)
        self.assertEqual(courses[0]["capacity"], 50)

    def test_courses_use_catalog_titles_and_academic_order(self):
        semester_one = Semester(
            id=1,
            name="Semester 1",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 1, 15),
            is_active=True,
        )
        semester_two = Semester(
            id=2,
            name="Semester 2",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 15),
            is_active=True,
        )
        courses = [
            Course(
                id=32,
                course_code="HUM101",
                title="Human Rights",
                credit_hours=2,
                faculty_id=1,
                department_id=4,
                level=1,
            ),
            Course(
                id=34,
                course_code="PHY101",
                title="Physics",
                credit_hours=3,
                faculty_id=1,
                department_id=4,
                level=1,
            ),
            Course(
                id=35,
                course_code="CS102",
                title="Computer Systems",
                credit_hours=3,
                faculty_id=1,
                department_id=4,
                level=1,
            ),
        ]
        offerings = [
            CourseOffering(id=41, course_id=32, semester_id=1, status="open"),
            CourseOffering(id=42, course_id=31, semester_id=1, status="open"),
            CourseOffering(id=43, course_id=34, semester_id=2, status="open"),
            CourseOffering(id=44, course_id=35, semester_id=1, status="open"),
        ]
        assignments = [
            CourseInstructor(id=54, course_offering_id=43, instructor_id=10),
            CourseInstructor(id=53, course_offering_id=41, instructor_id=10),
            CourseInstructor(id=52, course_offering_id=42, instructor_id=10),
            CourseInstructor(id=51, course_offering_id=44, instructor_id=11),
        ]
        cs101 = self.db.query(Course).filter(Course.id == 31).one()
        cs101.title = "Programming 1"
        self.db.add_all(
            [semester_one, semester_two, *courses, *offerings, *assignments]
        )
        self.db.commit()

        assigned_courses = get_faculty_courses(self.current_user, self.db)

        self.assertEqual(
            [course["course_code"] for course in assigned_courses],
            ["CS101", "HUM101", "PHY101", "CS201"],
        )
        self.assertEqual(assigned_courses[0]["course_title"], "Programming 1")
        self.assertEqual(assigned_courses[2]["course_title"], "Physics")
        self.assertNotIn(
            "CS102",
            [course["course_code"] for course in assigned_courses],
        )

    def test_enrollment_students_include_real_eligibility_statuses(self):
        payload = get_course_offering_enrollment_students(
            40,
            self.current_user,
            self.db,
        )
        by_id = {
            student["university_id"]: student
            for student in payload["students"]
        }

        self.assertEqual(payload["course"]["course_code"], "CS201")
        self.assertEqual(payload["course"]["current_enrolled_count"], 2)
        self.assertEqual(by_id["STU0001"]["status"], "already_enrolled")
        self.assertEqual(by_id["STU0003"]["status"], "not_eligible")
        self.assertIn("lower than course level", by_id["STU0003"]["reason"])
        self.assertEqual(by_id["STU0004"]["status"], "eligible")
        self.assertTrue(by_id["STU0004"]["is_selectable"])

    def test_faculty_can_enroll_an_eligible_student(self):
        response = enroll_students_in_course_offering(
            40,
            EnrollStudentsRequest(student_ids=[23]),
            self.current_user,
            self.db,
        )
        registration = (
            self.db.query(CourseRegistration)
            .filter(
                CourseRegistration.student_id == 23,
                CourseRegistration.course_offering_id == 40,
            )
            .first()
        )

        self.assertIsNotNone(registration)
        self.assertEqual(registration.status, "enrolled")
        self.assertEqual(response["current_enrolled_count"], 3)
        self.assertEqual(response["remaining_seats"], 47)

    def test_phy101_registration_connects_nour_to_assigned_faculty(self):
        semester = Semester(
            id=2,
            name="Semester 2",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 15),
            is_active=True,
        )
        physics = Course(
            id=32,
            course_code="PHY101",
            title="Physics",
            credit_hours=3,
            faculty_id=1,
            department_id=4,
            level=1,
        )
        offering = CourseOffering(
            id=41,
            course_id=physics.id,
            semester_id=semester.id,
            status="open",
        )
        assignment = CourseInstructor(
            id=51,
            course_offering_id=offering.id,
            instructor_id=10,
        )
        nour_user = User(
            id=7,
            university_id="STU-NOUR",
            full_name="Nour",
            email="nour@learnup.edu",
            password_hash="not-used",
            role="student",
            is_active=True,
        )
        nour = Student(
            id=24,
            user_id=nour_user.id,
            faculty_id=1,
            department_id=4,
            level=1,
            cgpa=3.4,
        )
        self.db.add_all(
            [
                semester,
                physics,
                offering,
                assignment,
                nour_user,
                nour,
                CourseRegistration(
                    student_id=nour.id,
                    course_offering_id=offering.id,
                    status="enrolled",
                ),
            ]
        )
        self.db.commit()

        roster = get_course_offering_registrations(
            offering.id,
            self.current_user,
            self.db,
        )
        enrollment_page = get_course_offering_enrollment_students(
            offering.id,
            self.current_user,
            self.db,
        )
        enrollment_by_id = {
            student["university_id"]: student
            for student in enrollment_page["students"]
        }

        self.assertEqual(roster["course"]["course_code"], "PHY101")
        self.assertEqual(
            [student["full_name"] for student in roster["students"]],
            ["Nour"],
        )
        self.assertEqual(
            enrollment_by_id["STU-NOUR"]["status"],
            "already_enrolled",
        )

    def test_unassigned_faculty_cannot_access_or_edit_offering(self):
        with self.assertRaises(HTTPException) as context:
            get_faculty_course_offering(
                40,
                self.other_instructor_user,
                self.db,
            )

        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
