from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_student
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.user import User
from app.schemas.chat import (
    ChatMessageOut,
    ChatRequest,
    ChatResponse,
    ChatSessionOut,
    ChatSourceItem,
    ChatStartResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/start", response_model=ChatStartResponse)
def start_chat_session(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    session = ChatSession(user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return ChatStartResponse(session_id=session.id, started_at=session.started_at)


@router.get("/my-sessions", response_model=List[ChatSessionOut])
def list_my_chat_sessions(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.id.desc())
        .all()
    )
    return [ChatSessionOut.model_validate(s) for s in rows]


def _get_owned_session(
    db: Session, session_id: int, user_id: int
) -> ChatSession:
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This chat session does not belong to you",
        )
    return session


@router.post("/{session_id}/message", response_model=ChatResponse)
def send_chat_message(
    session_id: int,
    body: ChatRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    from app.services import chatbot_service

    _get_owned_session(db, session_id, current_user.id)

    user_msg = ChatMessage(
        session_id=session_id,
        sender_type="user",
        message_text=body.message,
    )
    db.add(user_msg)
    db.flush()

    turn = chatbot_service.generate_chatbot_reply(body.message)
    stored_text = chatbot_service.format_stored_assistant_message(turn)
    assistant_msg = ChatMessage(
        session_id=session_id,
        sender_type="assistant",
        message_text=stored_text,
    )
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(
        session_id=session_id,
        user_message=body.message,
        assistant_response=turn.text,
        kb=turn.kb or None,
        sources=[ChatSourceItem(id=s.get("id"), title=s.get("title")) for s in turn.sources],
    )


@router.get("/{session_id}/messages", response_model=List[ChatMessageOut])
def list_session_messages(
    session_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    _get_owned_session(db, session_id, current_user.id)
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    return [ChatMessageOut.model_validate(m) for m in rows]
