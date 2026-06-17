from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.core.database import Base


class CourseRegistration(Base):
    __tablename__ = "course_registrations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, nullable=False)
    course_offering_id = Column(Integer, nullable=False)
    status = Column(String, default="registered")
    added_by_user_id = Column(Integer, nullable=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    final_grade = Column(String, nullable=True)
    is_passed = Column(Boolean, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
