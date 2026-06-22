import logging
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
_log = logging.getLogger("uvicorn.error")


def _get_owned_session(
    db: Session,
    session_id: int,
    user_id: int,
) -> ChatSession:
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id)
        .first()
    )
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


@router.post("/start", response_model=ChatStartResponse)
def start_chat_session(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    _log.info("active chat route called: POST /chat/start")
    _log.info("user_id: %s", current_user.id)

    session = ChatSession(user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)

    _log.info("session_id: %s", session.id)
    return ChatStartResponse(
        session_id=session.id,
        started_at=session.started_at,
    )


@router.get("/my-sessions", response_model=List[ChatSessionOut])
def list_my_chat_sessions(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    _log.info("active chat route called: GET /chat/my-sessions")
    _log.info("user_id: %s", current_user.id)

    rows = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.id.desc())
        .all()
    )

    _log.info("sessions count: %s", len(rows))
    return rows


@router.get("/{session_id:int}/messages", response_model=List[ChatMessageOut])
def list_session_messages(
    session_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    _log.info("active chat route called: GET /chat/{session_id}/messages")
    _log.info("user_id: %s", current_user.id)
    _log.info("session_id: %s", session_id)

    _get_owned_session(db, session_id, current_user.id)
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )

    _log.info("messages count: %s", len(rows))
    return rows


@router.post("/{session_id:int}/message", response_model=ChatResponse)
def send_chat_message(
    session_id: int,
    body: ChatRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    from app.services import chatbot_service

    _log.info("active chat route called: POST /chat/{session_id}/message")
    _log.info("user_id: %s", current_user.id)
    _log.info("session_id: %s", session_id)
    _log.info("message text length: %s", len(body.message))

    _get_owned_session(db, session_id, current_user.id)
    reply = chatbot_service.generate_chatbot_reply(body.message)

    
    reply_scope = getattr(reply, "scope", None) or getattr(reply, "kb", None) or "rag"
    _log.info("detected scope: %s", reply_scope)    
    _log.info("RAG used: %s", str(reply.rag_used).lower())
    _log.info("fallback used: %s", str(reply.fallback_used).lower())

    db.add_all(
        [
            ChatMessage(
                session_id=session_id,
                sender_type="user",
                message_text=body.message,
            ),
            ChatMessage(
                session_id=session_id,
                sender_type="assistant",
                message_text=reply.text,
            ),
        ]
    )
    db.commit()

    messages_count = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .count()
    )
    _log.info("messages count after save: %s", messages_count)

    return ChatResponse(
        session_id=session_id,
        user_message=body.message,
        assistant_response=reply.text,
        kb=reply.kb or None,
        sources=[
            ChatSourceItem(id=source.get("id"), title=source.get("title"))
            for source in reply.sources
        ],
    )
