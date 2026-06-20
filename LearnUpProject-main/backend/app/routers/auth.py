from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.department import Department
from app.models.instructor import Instructor
from app.models.student import Student
from app.models.user import User
from app.routers.student import _get_department_name, _get_student_profile
from app.schemas.auth import LoginRequest, LoginResponse, UserMeResponse
from app.services import auth_service
from app.services.academic_metrics import recalculate_student_academic_metrics

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = auth_service.create_access_token(user.id, str(user.role))
    return LoginResponse(access_token=token, token_type="bearer", role=str(user.role))


@router.get("/me", response_model=UserMeResponse)
def read_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = _get_student_profile(db, current_user)
    metrics = recalculate_student_academic_metrics(db, student)
    department_name = None
    advisor_name = None

    if student.department_id is not None:
        department_name = _get_department_name(db, student.department_id)

    if student.advisor_instructor_id is not None:
        instructor = db.query(Instructor).filter(Instructor.id == student.advisor_instructor_id).first()
        if instructor is not None:
            advisor_user = db.query(User).filter(User.id == instructor.user_id).first()
            if advisor_user is not None:
                advisor_name = advisor_user.full_name

    return UserMeResponse(
        id=int(current_user.id),
        university_id=str(current_user.university_id or ""),
        full_name=str(current_user.full_name or ""),
        email=str(current_user.email or ""),
        role=str(current_user.role or ""),
        student_id=int(student.id) if student.id is not None else None,
        department_id=student.department_id,
        department_name=department_name,
        level=student.level,
        advisor_instructor_id=student.advisor_instructor_id,
        advisor_name=advisor_name,
        cgpa=metrics["cgpa"],
        passed_credit_hours=metrics["passed_credit_hours"],
    )
