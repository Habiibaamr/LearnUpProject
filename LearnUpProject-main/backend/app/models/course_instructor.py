from sqlalchemy import Column, Integer

from app.core.database import Base


class CourseInstructor(Base):
    __tablename__ = "course_instructors"

    id = Column(Integer, primary_key=True, index=True)
    course_offering_id = Column(Integer, nullable=False)
    instructor_id = Column(Integer, nullable=False)
