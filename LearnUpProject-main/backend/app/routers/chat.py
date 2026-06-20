from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_student
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
    ChatbotHistoryResponse,
    ChatbotMessageRequest,
    ChatbotMessageResponse,
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


def _build_chat_context(current_user: User, db: Session) -> str:
    context_parts = [
        f"Role: {current_user.role}",
        f"Name: {current_user.full_name}",
        f"University ID: {current_user.university_id}",
    ]
    return "\n".join(context_parts)


@router.post("/chatbot/message", response_model=ChatbotMessageResponse)
def send_chatbot_message(
    body: ChatbotMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services import chatbot_service

    session = None
    if body.session_id is not None:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == body.session_id)
            .first()
        )
        if session is None or session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )
    else:
        session = ChatSession(user_id=current_user.id)
        db.add(session)
        db.flush()

    user_msg = ChatMessage(
        session_id=session.id,
        sender_type="user",
        message_text=body.message,
    )
    db.add(user_msg)
    db.flush()

    context = _build_chat_context(current_user, db)
    prompt = f"{context}\n\nStudent question: {body.message}"
    reply = chatbot_service.generate_chatbot_reply(prompt)
    assistant_text = reply.text.strip() if reply.text else (
        "I can help with academic advising, but the AI service is not configured yet. "
        "Please contact your academic advisor."
    )
    assistant_msg = ChatMessage(
        session_id=session.id,
        sender_type="ai",
        message_text=assistant_text,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatbotMessageResponse(
        session_id=session.id,
        reply=assistant_text,
        created_at=assistant_msg.created_at,
    )


@router.get("/chatbot/history", response_model=ChatbotHistoryResponse)
def get_chatbot_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.id.desc())
        .first()
    )
    if session is None:
        return ChatbotHistoryResponse(session_id=None, messages=[])

    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    return ChatbotHistoryResponse(
        session_id=session.id,
        messages=[ChatMessageOut.model_validate(row) for row in rows],
    )
