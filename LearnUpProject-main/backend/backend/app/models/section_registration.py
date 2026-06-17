from sqlalchemy import Column, DateTime, Integer, func

from app.core.database import Base


class SectionRegistration(Base):
    __tablename__ = "section_registrations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, nullable=False)
    section_group_id = Column(Integer, nullable=False)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
