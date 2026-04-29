import logging
from pathlib import Path

from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.core.database import Base, engine, get_db
from app.core.security import require_student
from app.routers import admin, auth, chat, instructor, student, test
from app.models import (  # noqa: F401 — register models with metadata
    Admin,
    ChatMessage,
    ChatSession,
    Course,
    CourseInstructor,
    CourseOffering,
    CoursePrerequisite,
    CourseRegistration,
    Department,
    Faculty,
    GradePostingWindow,
    Instructor,
    LectureGroup,
    LectureRegistration,
    SectionGroup,
    SectionRegistration,
    Semester,
    Student,
    SuperAdmin,
    User,
)

Base.metadata.create_all(bind=engine)

app = FastAPI()
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_UPLOADS_DIR = _BACKEND_ROOT / "uploads"
_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_UPLOADS_DIR)), name="uploads")

_log = logging.getLogger("uvicorn.error")


@app.on_event("startup")
def _log_loaded_code_paths() -> None:
    """If you still see old API behavior, confirm this path matches your Project/backend tree."""
    import app.routers.student as student_router

    _log.info("LearnUp student router file: %s", student_router.__file__)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(instructor.router)
app.include_router(student.router)
app.include_router(chat.router)
app.include_router(test.router)


@app.get("/learnup/student/identity-card")
def learnup_student_identity_card(
    response: Response,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """Identity card JSON — registered on the root app so it always matches this process."""
    return student._student_card_payload(db, current_user, response)


@app.get("/")
def root():
    return {"message": "LearnUp SIS backend is running"}


@app.get("/health")
def health() -> dict:
    """Public sanity check: open this URL in a browser to confirm *this* process is the LearnUp API."""
    import app.routers.student as student_router

    return {
        "ok": True,
        "learnup": True,
        "student_card_api": "v2-ensure-row",
        "identity_card_path": "/learnup/student/identity-card",
        "student_router_file": student_router.__file__,
    }
