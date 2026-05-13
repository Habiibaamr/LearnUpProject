import logging
import os
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

_log = logging.getLogger("uvicorn.error")
if engine is not None:
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        _log.exception("Database initialization failed during startup.")
else:
    _log.warning("DATABASE_URL is missing; DB-backed routes will return 503.")

app = FastAPI()
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_UPLOADS_DIR = (
    Path("/tmp/learnup-uploads") if os.getenv("VERCEL") else _BACKEND_ROOT / "uploads"
)
_UPLOADS_DIR = (
    Path(os.getenv("UPLOADS_DIR")).expanduser().resolve()
    if os.getenv("UPLOADS_DIR")
    else _DEFAULT_UPLOADS_DIR
)
_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_UPLOADS_DIR)), name="uploads")


def _cors_settings() -> tuple[list[str], bool]:
    local_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    raw = (os.getenv("CORS_ORIGINS") or "").strip()
    frontend_url = (os.getenv("FRONTEND_URL") or "").strip()
    if raw == "*":
        return ["*"], True

    origins: list[str] = []
    if raw:
        origins.extend(part.strip().rstrip("/") for part in raw.split(",") if part.strip())
    if frontend_url:
        origins.append(frontend_url.rstrip("/"))
    if not origins:
        origins = local_origins

    return list(dict.fromkeys(origins)), False


@app.on_event("startup")
def _log_loaded_code_paths() -> None:
    """If you still see old API behavior, confirm this path matches your Project/backend tree."""
    import app.routers.student as student_router

    _log.info("LearnUp student router file: %s", student_router.__file__)
    _log.info("LearnUp uploads directory: %s", _UPLOADS_DIR)
    if os.getenv("RENDER") and not os.getenv("UPLOADS_DIR"):
        _log.warning(
            "Using local uploads on Render. Files may not persist across deploys/restarts."
        )


_cors_origins, _allow_all_cors = _cors_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[] if _allow_all_cors else _cors_origins,
    allow_origin_regex=".*" if _allow_all_cors else None,
    allow_credentials=not _allow_all_cors,
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
        "database_configured": engine is not None,
        "student_card_api": "v2-ensure-row",
        "identity_card_path": "/learnup/student/identity-card",
        "uploads_dir": str(_UPLOADS_DIR),
        "student_router_file": student_router.__file__,
    }
