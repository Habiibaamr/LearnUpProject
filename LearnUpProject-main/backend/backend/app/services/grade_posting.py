from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.grade_posting_window import GradePostingWindow


def get_or_create_window(db: Session) -> GradePostingWindow:
    window = db.query(GradePostingWindow).order_by(GradePostingWindow.id.asc()).first()
    if window is not None:
        return window
    window = GradePostingWindow(is_open=False, term_index=None, updated_by_user_id=None)
    db.add(window)
    db.commit()
    db.refresh(window)
    return window


def get_window_status(db: Session) -> dict:
    window = get_or_create_window(db)
    return {
        "is_open": bool(window.is_open),
        "term_index": window.term_index,
        "updated_by_user_id": window.updated_by_user_id,
        "updated_at": window.updated_at,
    }


def set_window_status(
    db: Session,
    *,
    is_open: bool,
    term_index: int | None,
    admin_user_id: int,
) -> dict:
    window = get_or_create_window(db)
    window.is_open = is_open
    window.term_index = term_index if is_open else None
    window.updated_by_user_id = admin_user_id
    db.commit()
    db.refresh(window)
    return get_window_status(db)
