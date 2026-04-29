from sqlalchemy import Column, DateTime, Integer, String, func

from app.core.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False)
    sender_type = Column(String, nullable=False)
    message_text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
