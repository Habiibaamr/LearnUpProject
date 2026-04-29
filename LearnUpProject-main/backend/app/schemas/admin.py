from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CreateStudentAccountRequest(BaseModel):
    full_name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=1)
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    level: Optional[int] = None
    cgpa: Optional[float] = None
    passed_credit_hours: Optional[int] = None
    phone: Optional[str] = None
    advisor_instructor_id: Optional[int] = None


class CreateInstructorAccountRequest(BaseModel):
    full_name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=1)
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    specialization: Optional[str] = None
    office_location: Optional[str] = None
    phone: Optional[str] = None


class CreateAdminAccountRequest(BaseModel):
    full_name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=1)
    position: Optional[str] = None


class UpdateAdminAccountRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=1)
    position: Optional[str] = None
    is_active: Optional[bool] = None


class AssignInstructorRequest(BaseModel):
    course_offering_id: int
    instructor_id: int


class CompleteStudentTermRequest(BaseModel):
    """Mark an entire catalog term (six courses) complete for a student. Admin only."""

    university_id: str = Field(min_length=1)
    term_index: int = Field(ge=0, le=7, description="0 = Level 1 semester 1, …, 7 = Level 4 semester 2")


class CompleteAllStudentsTermRequest(BaseModel):
    """Mark an entire catalog term (six courses) complete for all students. Admin only."""

    term_index: int = Field(
        ge=0,
        le=7,
        description="0 = Level 1 semester 1, …, 7 = Level 4 semester 2",
    )


class OpenFinalGradesWindowRequest(BaseModel):
    """Open final grade posting for a specific catalog term."""

    term_index: int = Field(
        ge=0,
        le=7,
        description="0 = Level 1 semester 1, …, 7 = Level 4 semester 2",
    )
