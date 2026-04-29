from sqlalchemy import Column, Integer, String

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    credit_hours = Column(Integer, nullable=False)
    faculty_id = Column(Integer, nullable=False)
    department_id = Column(Integer, nullable=False)
    level = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
