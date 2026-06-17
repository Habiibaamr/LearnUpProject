from sqlalchemy import Boolean, Column, DateTime, Integer, func

from app.core.database import Base


class GradePostingWindow(Base):
    __tablename__ = "grade_posting_window"

    id = Column(Integer, primary_key=True, index=True)
    is_open = Column(Boolean, nullable=False, default=False)
    term_index = Column(Integer, nullable=True)
    updated_by_user_id = Column(Integer, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
