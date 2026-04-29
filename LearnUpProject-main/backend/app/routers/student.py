from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi import File, Request, UploadFile
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_student
from app.services import registration_rules
from app.services import course_enrollment
from app.models.course import Course
from app.models.course_offering import CourseOffering
from app.models.course_registration import CourseRegistration
from app.models.lecture_group import LectureGroup
from app.models.lecture_registration import LectureRegistration
from app.models.section_group import SectionGroup
from app.models.section_registration import SectionRegistration
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.instructor import Instructor
from app.models.student import Student
from app.models.user import User

router = APIRouter(prefix="/student", tags=["student"])
TOTAL_PROGRAM_CREDIT_HOURS = 140
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_PROFILE_IMAGE_BYTES = 5 * 1024 * 1024


def _get_student_profile(db: Session, current_user: User) -> Student:
    """Return the student's row, creating a minimal profile if missing.

    Logic is inlined here so this file alone defines behavior (no accidental import
    of another ``student_profile`` module from ``sys.path``).
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if student is not None:
        return student
    student = Student(user_id=current_user.id)
    db.add(student)
    try:
        db.commit()
        db.refresh(student)
        return student
    except IntegrityError:
        db.rollback()
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not load student profile",
            ) from None
        return student
    except SQLAlchemyError:
        db.rollback()
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not load student profile",
            ) from None
        return student


def _require_active_course_registration(
    db: Session, student: Student, course_offering_id: int
) -> None:
    reg = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.student_id == student.id,
            CourseRegistration.course_offering_id == course_offering_id,
            CourseRegistration.status == "registered",
        )
        .first()
    )
    if reg is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not registered for this course offering",
        )


def _student_card_payload(
    db: Session, current_user: User, response: Response
) -> dict:
    student = _get_student_profile(db, current_user)
    response.headers["X-LearnUp-Student-Card"] = "v2"
    faculty_name = None
    faculty_code = None
    department_name = None
    department_code = None
    if student.faculty_id is not None:
        fac = db.query(Faculty).filter(Faculty.id == student.faculty_id).first()
        if fac is not None:
            faculty_name = fac.name
            faculty_code = fac.code
    if student.department_id is not None:
        dep = db.query(Department).filter(Department.id == student.department_id).first()
        if dep is not None:
            department_name = dep.name
            department_code = dep.code
    advisor_name = None
    if student.advisor_instructor_id is not None:
        inst = (
            db.query(Instructor)
            .filter(Instructor.id == student.advisor_instructor_id)
            .first()
        )
        if inst is not None:
            adv_user = db.query(User).filter(User.id == inst.user_id).first()
            if adv_user is not None:
                advisor_name = adv_user.full_name
    return {
        "student_card_api": "v2-ensure-row",
        "user_id": current_user.id,
        "university_id": current_user.university_id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "photo_url": student.photo_url,
        "faculty_id": student.faculty_id,
        "faculty_name": faculty_name,
        "faculty_code": faculty_code,
        "department_id": student.department_id,
        "department_name": department_name,
        "department_code": department_code,
        "level": student.level,
        "cgpa": student.cgpa,
        "passed_credit_hours": student.passed_credit_hours,
        "total_credit_hours": TOTAL_PROGRAM_CREDIT_HOURS,
        "phone": student.phone,
        "advisor_instructor_id": student.advisor_instructor_id,
        "advisor_name": advisor_name,
    }


@router.get("/me/card")
def get_my_student_card(
    response: Response,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """Legacy path; prefer ``/v2/me/card`` for the identity UI."""
    return _student_card_payload(db, current_user, response)


@router.get("/v2/me/card")
def get_my_student_card_v2(
    response: Response,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """Identity card data — new path so stale deployments cannot shadow this handler."""
    return _student_card_payload(db, current_user, response)


@router.post("/me/photo")
def upload_my_photo(
    request: Request,
    photo: UploadFile = File(...),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = _get_student_profile(db, current_user)
    content_type = (photo.content_type or "").lower().strip()
    ext = ALLOWED_IMAGE_CONTENT_TYPES.get(content_type)
    if ext is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image type. Use JPG, PNG, or WEBP.",
        )

    backend_root = Path(__file__).resolve().parent.parent.parent
    uploads_dir = backend_root / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    filename = f"student_{student.id}_{uuid4().hex}{ext}"
    file_path = uploads_dir / filename

    bytes_written = 0
    with file_path.open("wb") as out_file:
        while True:
            chunk = photo.file.read(1024 * 1024)
            if not chunk:
                break
            bytes_written += len(chunk)
            if bytes_written > MAX_PROFILE_IMAGE_BYTES:
                out_file.close()
                file_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image too large. Max size is 5MB.",
                )
            out_file.write(chunk)

    old_photo_url = student.photo_url
    photo_url = request.url_for("uploads", path=filename)
    student.photo_url = str(photo_url)
    db.commit()
    db.refresh(student)

    if old_photo_url and "/uploads/" in old_photo_url:
        old_filename = old_photo_url.rsplit("/uploads/", 1)[-1]
        old_path = uploads_dir / old_filename
        old_path.unlink(missing_ok=True)

    return {"message": "Profile photo updated", "photo_url": student.photo_url}


@router.get("/me/courses")
def list_my_registered_courses(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = _get_student_profile(db, current_user)
    registrations = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.student_id == student.id,
            CourseRegistration.status == "registered",
        )
        .all()
    )
    result = []
    for reg in registrations:
        offering = (
            db.query(CourseOffering)
            .filter(CourseOffering.id == reg.course_offering_id)
            .first()
        )
        if offering is None:
            continue
        course = db.query(Course).filter(Course.id == offering.course_id).first()
        if course is None:
            continue
        result.append(
            {
                "registration_id": reg.id,
                "course_offering_id": reg.course_offering_id,
                "course_id": course.id,
                "course_code": course.course_code,
                "course_title": course.title,
                "credit_hours": course.credit_hours,
                "semester_id": offering.semester_id,
                "registration_status": reg.status,
                "registered_at": reg.registered_at,
            }
        )
    return result


@router.get("/me/course-board")
def get_course_board(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = _get_student_profile(db, current_user)
    return {"courses": course_enrollment.build_course_board(db, student)}


@router.post("/me/add-course-by-course/{course_id}")
def add_course_by_course(
    course_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = _get_student_profile(db, current_user)
    return course_enrollment.enroll_student_by_course_id(
        db, student, course_id, acting_user_id=current_user.id
    )


@router.post("/me/drop-course-by-course/{course_id}")
def drop_course_by_course(
    course_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = _get_student_profile(db, current_user)
    return course_enrollment.drop_student_by_course_id(db, student, course_id)


@router.post("/me/add-course/{course_offering_id}")
def add_course(
    course_offering_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = _get_student_profile(db, current_user)

    existing = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.student_id == student.id,
            CourseRegistration.course_offering_id == course_offering_id,
            CourseRegistration.status == "registered",
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already registered for this course offering",
        )

    registration_rules.validate_course_registration_rules(
        db, student, course_offering_id
    )

    registration = CourseRegistration(
        student_id=student.id,
        course_offering_id=course_offering_id,
        status="registered",
        added_by_user_id=current_user.id,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)

    return {
        "message": "Course added successfully",
        "registration": {
            "id": registration.id,
            "student_id": registration.student_id,
            "course_offering_id": registration.course_offering_id,
            "status": registration.status,
            "added_by_user_id": registration.added_by_user_id,
            "registered_at": registration.registered_at,
        },
    }


@router.post("/me/drop-course/{course_offering_id}")
def drop_course(
    course_offering_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = _get_student_profile(db, current_user)

    registration = (
        db.query(CourseRegistration)
        .filter(
            CourseRegistration.student_id == student.id,
            CourseRegistration.course_offering_id == course_offering_id,
            CourseRegistration.status == "registered",
        )
        .first()
    )
    if registration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active registration not found for this course offering",
        )

    registration.status = "dropped"
    db.commit()
    db.refresh(registration)

    return {
        "message": "Course dropped successfully",
        "registration": {
            "id": registration.id,
            "student_id": registration.student_id,
            "course_offering_id": registration.course_offering_id,
            "status": registration.status,
            "added_by_user_id": registration.added_by_user_id,
            "registered_at": registration.registered_at,
        },
    }


@router.get("/me/available-groups/{course_offering_id}")
def list_available_groups(
    course_offering_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = _get_student_profile(db, current_user)
    _require_active_course_registration(db, student, course_offering_id)

    lecture_groups = (
        db.query(LectureGroup)
        .filter(LectureGroup.course_offering_id == course_offering_id)
        .all()
    )
    section_groups = (
        db.query(SectionGroup)
        .filter(SectionGroup.course_offering_id == course_offering_id)
        .all()
    )

    lecture_payload = []
    for g in lecture_groups:
        cap = g.capacity if g.capacity is not None else 100
        current_count = (
            db.query(LectureRegistration)
            .filter(LectureRegistration.lecture_group_id == g.id)
            .count()
        )
        lecture_payload.append(
            {
                "id": g.id,
                "group_code": g.group_code,
                "instructor_id": g.instructor_id,
                "day_of_week": g.day_of_week,
                "start_time": g.start_time,
                "end_time": g.end_time,
                "room": g.room,
                "capacity": cap,
                "current_count": current_count,
                "remaining_capacity": max(0, cap - current_count),
            }
        )

    section_payload = []
    for g in section_groups:
        cap = g.capacity if g.capacity is not None else 30
        current_count = (
            db.query(SectionRegistration)
            .filter(SectionRegistration.section_group_id == g.id)
            .count()
        )
        section_payload.append(
            {
                "id": g.id,
                "group_code": g.group_code,
                "instructor_id": g.instructor_id,
                "day_of_week": g.day_of_week,
                "start_time": g.start_time,
                "end_time": g.end_time,
                "room": g.room,
                "capacity": cap,
                "current_count": current_count,
                "remaining_capacity": max(0, cap - current_count),
            }
        )

    return {
        "course_offering_id": course_offering_id,
        "lecture_groups": lecture_payload,
        "section_groups": section_payload,
    }


@router.post("/me/register-lecture/{lecture_group_id}")
def register_lecture(
    lecture_group_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = _get_student_profile(db, current_user)

    lecture_group = (
        db.query(LectureGroup).filter(LectureGroup.id == lecture_group_id).first()
    )
    if lecture_group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture group not found",
        )

    offering_id = lecture_group.course_offering_id
    _require_active_course_registration(db, student, offering_id)

    sibling_groups = (
        db.query(LectureGroup)
        .filter(LectureGroup.course_offering_id == offering_id)
        .all()
    )
    sibling_ids = [g.id for g in sibling_groups]
    existing_lecture = (
        db.query(LectureRegistration)
        .filter(
            LectureRegistration.student_id == student.id,
            LectureRegistration.lecture_group_id.in_(sibling_ids),
        )
        .first()
    )
    if existing_lecture is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already registered for a lecture group in this course offering",
        )

    cap = lecture_group.capacity if lecture_group.capacity is not None else 100
    current_count = (
        db.query(LectureRegistration)
        .filter(LectureRegistration.lecture_group_id == lecture_group_id)
        .count()
    )
    if current_count >= cap:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lecture group is full",
        )

    reg = LectureRegistration(
        student_id=student.id,
        lecture_group_id=lecture_group_id,
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)

    return {
        "message": "Lecture group registration successful",
        "registration": {
            "id": reg.id,
            "student_id": reg.student_id,
            "lecture_group_id": reg.lecture_group_id,
            "registered_at": reg.registered_at,
        },
    }


@router.post("/me/register-section/{section_group_id}")
def register_section(
    section_group_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = _get_student_profile(db, current_user)

    section_group = (
        db.query(SectionGroup).filter(SectionGroup.id == section_group_id).first()
    )
    if section_group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section group not found",
        )

    offering_id = section_group.course_offering_id
    _require_active_course_registration(db, student, offering_id)

    sibling_groups = (
        db.query(SectionGroup)
        .filter(SectionGroup.course_offering_id == offering_id)
        .all()
    )
    sibling_ids = [g.id for g in sibling_groups]
    existing_section = (
        db.query(SectionRegistration)
        .filter(
            SectionRegistration.student_id == student.id,
            SectionRegistration.section_group_id.in_(sibling_ids),
        )
        .first()
    )
    if existing_section is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already registered for a section group in this course offering",
        )

    cap = section_group.capacity if section_group.capacity is not None else 30
    current_count = (
        db.query(SectionRegistration)
        .filter(SectionRegistration.section_group_id == section_group_id)
        .count()
    )
    if current_count >= cap:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section group is full",
        )

    reg = SectionRegistration(
        student_id=student.id,
        section_group_id=section_group_id,
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)

    return {
        "message": "Section group registration successful",
        "registration": {
            "id": reg.id,
            "student_id": reg.student_id,
            "section_group_id": reg.section_group_id,
            "registered_at": reg.registered_at,
        },
    }


@router.post("/me/drop-lecture/{lecture_group_id}")
def drop_lecture(
    lecture_group_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = _get_student_profile(db, current_user)

    reg = (
        db.query(LectureRegistration)
        .filter(
            LectureRegistration.student_id == student.id,
            LectureRegistration.lecture_group_id == lecture_group_id,
        )
        .first()
    )
    if reg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture registration not found",
        )

    db.delete(reg)
    db.commit()

    return {"message": "Lecture group registration dropped successfully"}


@router.post("/me/drop-section/{section_group_id}")
def drop_section(
    section_group_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = _get_student_profile(db, current_user)

    reg = (
        db.query(SectionRegistration)
        .filter(
            SectionRegistration.student_id == student.id,
            SectionRegistration.section_group_id == section_group_id,
        )
        .first()
    )
    if reg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section registration not found",
        )

    db.delete(reg)
    db.commit()

    return {"message": "Section group registration dropped successfully"}
