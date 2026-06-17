from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @field_validator("password", mode="before")
    @classmethod
    def strip_password(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserMeResponse(BaseModel):
    id: int
    university_id: str
    full_name: str
    email: str
    role: str
