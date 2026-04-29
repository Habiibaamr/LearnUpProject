import bcrypt
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    ROLE_ADMIN,
    ROLE_INSTRUCTOR,
    ROLE_SUPER_ADMIN,
    ROLE_STUDENT,
    require_admin,
    require_admin_portal_user,
    require_super_admin,
)
from app.models.admin import Admin as AdminProfile
from app.models.course import Course
from app.models.course_instructor import CourseInstructor
from app.models.course_offering import CourseOffering
from app.models.instructor import Instructor
from app.models.student import Student
from app.models.super_admin import SuperAdmin as SuperAdminProfile
from app.models.user import User
from app.schemas.admin import (
    AssignInstructorRequest,
    CompleteAllStudentsTermRequest,
    CompleteStudentTermRequest,
    CreateAdminAccountRequest,
    CreateInstructorAccountRequest,
    CreateStudentAccountRequest,
    OpenFinalGradesWindowRequest,
    UpdateAdminAccountRequest,
)
from app.services.academic_terms import (
    complete_term_for_all_students,
    complete_term_for_student,
)
from app.services.grade_posting import get_window_status, set_window_status

router = APIRouter(prefix="/admin", tags=["admin"])


def _generate_university_id(db: Session, role: str) -> str:
    prefix_map = {
        ROLE_STUDENT: "STD",
        ROLE_INSTRUCTOR: "INS",
        ROLE_ADMIN: "ADM",
        ROLE_SUPER_ADMIN: "SAD",
    }
    prefix = prefix_map.get(role, "USR")
    rows = db.query(User.university_id).filter(User.role == role).all()
    max_num = 0
    pattern = re.compile(rf"^{prefix}(\d+)$")
    for row in rows:
        university_id = row[0] if isinstance(row, tuple) else row.university_id
        m = pattern.match(str(university_id))
        if not m:
            continue
        max_num = max(max_num, int(m.group(1)))
    next_num = max_num + 1
    candidate = f"{prefix}{next_num:04d}"
    while db.query(User).filter(User.university_id == candidate).first() is not None:
        next_num += 1
        candidate = f"{prefix}{next_num:04d}"
    return candidate


def _user_public_dict(db: Session, u: User) -> dict:
    position = None
    if u.role == ROLE_ADMIN:
        admin_profile = (
            db.query(AdminProfile)
            .filter(AdminProfile.user_id == u.id)
            .first()
        )
        position = admin_profile.position if admin_profile is not None else None
    elif u.role == ROLE_SUPER_ADMIN:
        super_admin_profile = (
            db.query(SuperAdminProfile)
            .filter(SuperAdminProfile.user_id == u.id)
            .first()
        )
        position = (
            super_admin_profile.position if super_admin_profile is not None else None
        )
    return {
        "id": u.id,
        "university_id": u.university_id,
        "full_name": u.full_name,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active,
        "position": position,
        "created_at": u.created_at,
    }


def _get_admin_user_by_id(db: Session, user_id: int) -> User | None:
    return (
        db.query(User)
        .filter(User.id == user_id, User.role == ROLE_ADMIN)
        .first()
    )


@router.get("/users")
def list_users(
    _admin: User = Depends(require_admin_portal_user),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id.desc()).all()
    return [_user_public_dict(db, u) for u in users]


@router.get("/instructors")
def list_instructors(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(Instructor).order_by(Instructor.id.asc()).all()
    result = []
    for row in rows:
        user = db.query(User).filter(User.id == row.user_id).first()
        if user is None:
            continue
        result.append(
            {
                "instructor_id": row.id,
                "user_id": user.id,
                "university_id": user.university_id,
                "full_name": user.full_name,
                "email": user.email,
            }
        )
    return result


@router.get("/course-offerings")
def list_course_offerings(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(CourseOffering).order_by(CourseOffering.id.asc()).all()
    result = []
    for row in rows:
        course = db.query(Course).filter(Course.id == row.course_id).first()
        if course is None:
            continue
        result.append(
            {
                "course_offering_id": row.id,
                "course_id": course.id,
                "course_code": course.course_code,
                "course_title": course.title,
                "semester_id": row.semester_id,
                "status": row.status,
            }
        )
    return result


@router.post("/create-student-account")
def create_student_account(
    body: CreateStudentAccountRequest,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == body.email).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    generated_university_id = _generate_university_id(db, role="student")

    password_hash = bcrypt.hashpw(body.password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    user = User(
        university_id=generated_university_id,
        full_name=body.full_name,
        email=body.email,
        password_hash=password_hash,
        role="student",
        is_active=True,
    )
    db.add(user)
    db.flush()

    student = Student(
        user_id=user.id,
        faculty_id=body.faculty_id,
        department_id=body.department_id,
        level=body.level,
        cgpa=body.cgpa,
        passed_credit_hours=body.passed_credit_hours,
        phone=body.phone,
        advisor_instructor_id=body.advisor_instructor_id,
    )
    db.add(student)
    db.commit()
    db.refresh(user)
    db.refresh(student)

    return {
        "user": _user_public_dict(db, user),
        "student": {
            "id": student.id,
            "user_id": student.user_id,
            "photo_url": student.photo_url,
            "faculty_id": student.faculty_id,
            "department_id": student.department_id,
            "level": student.level,
            "cgpa": student.cgpa,
            "passed_credit_hours": student.passed_credit_hours,
            "phone": student.phone,
            "advisor_instructor_id": student.advisor_instructor_id,
            "created_at": student.created_at,
        },
    }


@router.post("/create-instructor-account")
def create_instructor_account(
    body: CreateInstructorAccountRequest,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == body.email).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    generated_university_id = _generate_university_id(db, role="instructor")

    password_hash = bcrypt.hashpw(body.password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    user = User(
        university_id=generated_university_id,
        full_name=body.full_name,
        email=body.email,
        password_hash=password_hash,
        role="instructor",
        is_active=True,
    )
    db.add(user)
    db.flush()

    instructor = Instructor(
        user_id=user.id,
        faculty_id=body.faculty_id,
        department_id=body.department_id,
        specialization=body.specialization,
        office_location=body.office_location,
        phone=body.phone,
    )
    db.add(instructor)
    db.commit()
    db.refresh(user)
    db.refresh(instructor)

    return {
        "user": _user_public_dict(db, user),
        "instructor": {
            "id": instructor.id,
            "user_id": instructor.user_id,
            "faculty_id": instructor.faculty_id,
            "department_id": instructor.department_id,
            "specialization": instructor.specialization,
            "office_location": instructor.office_location,
            "phone": instructor.phone,
            "created_at": instructor.created_at,
        },
    }


@router.post("/create-admin-account")
def create_admin_account(
    body: CreateAdminAccountRequest,
    _super_admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == body.email).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    generated_university_id = _generate_university_id(db, role=ROLE_ADMIN)

    password_hash = bcrypt.hashpw(body.password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    user = User(
        university_id=generated_university_id,
        full_name=body.full_name,
        email=body.email,
        password_hash=password_hash,
        role=ROLE_ADMIN,
        is_active=True,
    )
    db.add(user)
    db.flush()

    admin_profile = AdminProfile(user_id=user.id, position=body.position)
    db.add(admin_profile)
    db.commit()
    db.refresh(user)
    db.refresh(admin_profile)

    return {
        "user": _user_public_dict(db, user),
        "admin": {
            "id": admin_profile.id,
            "user_id": admin_profile.user_id,
            "position": admin_profile.position,
            "created_at": admin_profile.created_at,
        },
    }


@router.patch("/admin-accounts/{user_id}")
def update_admin_account(
    user_id: int,
    body: UpdateAdminAccountRequest,
    _super_admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    user = _get_admin_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin account not found",
        )

    admin_profile = (
        db.query(AdminProfile)
        .filter(AdminProfile.user_id == user.id)
        .first()
    )
    if admin_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin profile not found",
        )

    if body.email and body.email != user.email:
        existing = db.query(User).filter(User.email == body.email).first()
        if existing is not None and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    if body.full_name is not None:
        user.full_name = body.full_name
    if body.email is not None:
        user.email = body.email
    if body.password is not None:
        user.password_hash = bcrypt.hashpw(
            body.password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.position is not None:
        admin_profile.position = body.position

    db.commit()
    db.refresh(user)
    db.refresh(admin_profile)

    return {
        "message": "Admin account updated successfully",
        "user": _user_public_dict(db, user),
        "admin": {
            "id": admin_profile.id,
            "user_id": admin_profile.user_id,
            "position": admin_profile.position,
            "created_at": admin_profile.created_at,
        },
    }


@router.delete("/admin-accounts/{user_id}")
def delete_admin_account(
    user_id: int,
    _super_admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    user = _get_admin_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin account not found",
        )

    admin_profile = (
        db.query(AdminProfile)
        .filter(AdminProfile.user_id == user.id)
        .first()
    )
    if admin_profile is not None:
        db.delete(admin_profile)
    db.delete(user)
    db.commit()

    return {"message": "Admin account deleted successfully"}


@router.post("/assign-instructor-to-offering")
def assign_instructor_to_offering(
    body: AssignInstructorRequest,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    offering = (
        db.query(CourseOffering)
        .filter(CourseOffering.id == body.course_offering_id)
        .first()
    )
    if offering is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course offering not found",
        )

    instructor = (
        db.query(Instructor).filter(Instructor.id == body.instructor_id).first()
    )
    if instructor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found",
        )

    existing = (
        db.query(CourseInstructor)
        .filter(
            CourseInstructor.course_offering_id == body.course_offering_id,
            CourseInstructor.instructor_id == body.instructor_id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instructor already assigned to this course offering",
        )

    row = CourseInstructor(
        course_offering_id=body.course_offering_id,
        instructor_id=body.instructor_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "message": "Instructor assigned to course offering successfully",
        "course_instructor": {
            "id": row.id,
            "course_offering_id": row.course_offering_id,
            "instructor_id": row.instructor_id,
        },
    }


@router.post("/complete-student-term")
def complete_student_term(
    body: CompleteStudentTermRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Record that the student finished all six courses in a catalog term; opens the next term."""
    user = (
        db.query(User)
        .filter(User.university_id == body.university_id, User.role == ROLE_STUDENT)
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student user not found for this university_id",
        )
    student = db.query(Student).filter(Student.user_id == user.id).first()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )
    try:
        result = complete_term_for_student(
            db, student, body.term_index, acting_admin_user_id=admin_user.id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {"message": "Term completion recorded", **result}


@router.post("/complete-term-all-students")
def complete_term_all_students(
    body: CompleteAllStudentsTermRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Record completion of one catalog term for all students at once."""
    try:
        result = complete_term_for_all_students(
            db,
            body.term_index,
            acting_admin_user_id=admin_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {"message": "Bulk term completion finished", **result}


@router.get("/final-grades-window")
def get_final_grades_window(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return get_window_status(db)


@router.post("/final-grades-window/open")
def open_final_grades_window(
    body: OpenFinalGradesWindowRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    status_payload = set_window_status(
        db,
        is_open=True,
        term_index=body.term_index,
        admin_user_id=admin_user.id,
    )
    return {"message": "Final grades window opened", **status_payload}


@router.post("/final-grades-window/close")
def close_final_grades_window(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    status_payload = set_window_status(
        db,
        is_open=False,
        term_index=None,
        admin_user_id=admin_user.id,
    )
    return {"message": "Final grades window closed", **status_payload}


@router.get("/course-offering-instructors/{course_offering_id}")
def list_course_offering_instructors(
    course_offering_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    offering = (
        db.query(CourseOffering)
        .filter(CourseOffering.id == course_offering_id)
        .first()
    )
    if offering is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course offering not found",
        )

    rows = (
        db.query(CourseInstructor)
        .filter(CourseInstructor.course_offering_id == course_offering_id)
        .all()
    )
    return [
        {
            "id": r.id,
            "course_offering_id": r.course_offering_id,
            "instructor_id": r.instructor_id,
        }
        for r in rows
    ]
