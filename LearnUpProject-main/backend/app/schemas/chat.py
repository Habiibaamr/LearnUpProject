from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatSourceItem(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: int
    user_message: str
    assistant_response: str
    kb: Optional[str] = None
    sources: List[ChatSourceItem] = Field(default_factory=list)


class ChatStartResponse(BaseModel):
    session_id: int
    started_at: datetime


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    sender_type: str
    message_text: str
    created_at: datetime


class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
