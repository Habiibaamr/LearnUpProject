from sqlalchemy import Column, Integer, String

from app.core.database import Base


class CourseOffering(Base):
    __tablename__ = "course_offerings"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, nullable=False)
    semester_id = Column(Integer, nullable=False)
    coordinator_instructor_id = Column(Integer, nullable=True)
    status = Column(String, default="open")
