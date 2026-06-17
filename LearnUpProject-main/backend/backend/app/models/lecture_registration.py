from sqlalchemy import Column, DateTime, Integer, func

from app.core.database import Base


class LectureRegistration(Base):
    __tablename__ = "lecture_registrations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, nullable=False)
    lecture_group_id = Column(Integer, nullable=False)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
