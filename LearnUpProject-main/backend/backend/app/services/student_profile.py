from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.student import Student


def get_or_create_student_row(db: Session, user_id: int) -> Student:
    """Return ``students`` row for ``user_id``, inserting a minimal row if absent."""
    student = db.query(Student).filter(Student.user_id == user_id).first()
    if student is not None:
        return student
    student = Student(user_id=user_id)
    db.add(student)
    try:
        db.commit()
        db.refresh(student)
        return student
    except IntegrityError:
        db.rollback()
        student = db.query(Student).filter(Student.user_id == user_id).first()
        if student is None:
            raise RuntimeError("student row missing after concurrent create") from None
        return student
    except SQLAlchemyError:
        # Rare races or DB-specific errors on insert — always fall back to a SELECT.
        db.rollback()
        student = db.query(Student).filter(Student.user_id == user_id).first()
        if student is None:
            raise
        return student
