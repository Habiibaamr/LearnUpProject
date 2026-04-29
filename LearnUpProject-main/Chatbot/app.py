"""
Standalone Graduation Assistant API — uses the same RAG code as LearnUp (one source of truth).

Run from repo root (so `backend` is on the path), e.g.:
  cd <Project>
  python -m uvicorn Chatbot.app:app --reload --port 8010

Or from Chatbot folder after setting PYTHONPATH to ../backend.
"""
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

_ROOT = Path(__file__).resolve().parent
_BACKEND = _ROOT.parent / "backend"
if _BACKEND.is_dir() and str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.services.chatbot_service import ChatRequest, build_standalone_engine

engine = build_standalone_engine(_ROOT)

app = FastAPI()


@app.post("/chat")
async def chat(req: ChatRequest):
    kb, answer, sources = engine.search(req.message)
    return {"kb": kb, "answer": answer, "sources": sources}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    index_path = _ROOT / "index.html"
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
