from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserMeResponse
from app.services import auth_service

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
def read_me(current_user: User = Depends(get_current_user)):
    return UserMeResponse(
        id=int(current_user.id),
        university_id=str(current_user.university_id or ""),
        full_name=str(current_user.full_name or ""),
        email=str(current_user.email or ""),
        role=str(current_user.role or ""),
    )
