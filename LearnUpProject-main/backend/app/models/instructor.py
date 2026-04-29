from sqlalchemy import Column, DateTime, Integer, String, func

from app.core.database import Base


class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True)
    faculty_id = Column(Integer, nullable=True)
    department_id = Column(Integer, nullable=True)
    specialization = Column(String, nullable=True)
    office_location = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
