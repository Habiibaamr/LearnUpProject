from sqlalchemy import Column, DateTime, Float, Integer, String, func

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True)
    photo_url = Column(String, nullable=True)
    faculty_id = Column(Integer, nullable=True)
    department_id = Column(Integer, nullable=True)
    level = Column(Integer, nullable=True)
    cgpa = Column(Float, nullable=True)
    passed_credit_hours = Column(Integer, nullable=True)
    phone = Column(String, nullable=True)
    advisor_instructor_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
