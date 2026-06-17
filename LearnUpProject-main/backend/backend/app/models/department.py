from sqlalchemy import Column, Integer, String

from app.core.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    faculty_id = Column(Integer, nullable=False)
