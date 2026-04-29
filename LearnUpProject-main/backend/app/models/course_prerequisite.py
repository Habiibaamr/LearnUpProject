from sqlalchemy import Column, Integer

from app.core.database import Base


class CoursePrerequisite(Base):
    __tablename__ = "course_prerequisites"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, nullable=False)
    prerequisite_course_id = Column(Integer, nullable=False)
