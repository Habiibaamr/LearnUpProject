from sqlalchemy import Column, Integer, String, Time

from app.core.database import Base


class LectureGroup(Base):
    __tablename__ = "lecture_groups"

    id = Column(Integer, primary_key=True, index=True)
    course_offering_id = Column(Integer, nullable=False)
    group_code = Column(String, nullable=False)
    instructor_id = Column(Integer, nullable=True)
    day_of_week = Column(String, nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    room = Column(String, nullable=True)
    capacity = Column(Integer, default=100)
