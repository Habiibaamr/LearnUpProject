"""
Core RAG chatbot logic (no FastAPI app here).

Imported by:
  - Chatbot/app.py  → POST /chat returns { kb, answer, sources }
  - LearnUp backend → app.services.chatbot_service (student portal)

Set OPENAI_API_KEY in backend/.env (or Chatbot/.env); never commit keys to source code.
"""
import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import faiss
import numpy as np
from openai import OpenAI
from pydantic import BaseModel

# --- Configuration ---


@dataclass
class Config:
    """Same settings as your standalone bot; paths are usually set by app.py / SIS adapter."""

    OPENAI_API_KEY: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", "").strip())
    CHAT_MODEL: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    EMBED_MODEL: str = field(
        default_factory=lambda: os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    )
    DATA_DIR: str = ""
    INDEX_DIR: str = ""

    def __post_init__(self) -> None:
        if not self.DATA_DIR:
            self.DATA_DIR = os.getcwd()
        if not self.INDEX_DIR:
            self.INDEX_DIR = os.path.join(self.DATA_DIR, "indexes")


KBS = {
    "ADVISING": "massive_academic_advising_kb.md",
    "POLICIES": "policies.md",
    "WELLBEING": "wellbeing.md",
    "REGISTRATION": "registration_rules.md",
}

# --- System Instructions ---

BASE_PROMPT = """You are the 'Graduation Assistant', a premium university AI advisor. 
Provide accurate, helpful, and empathetic guidance based ONLY on the provided context.

### GUIDELINES:
1. **Source Attribution**: Always cite information using the [ID] from the context (e.g., [REG-2026-0]).
2. **Formatting**: Use Markdown. Use **bold** for deadlines/metrics and bullet points for lists.
3. **Tone**: Be professional and encouraging. 
4. **Accuracy**: If the answer is not in context, state that you don't have that specific record and suggest visiting an advisor.
5. **Language**: Support both English and Arabic based on the user's query.
"""

CATEGORY_PROMPTS = {
    "ADVISING": "Persona: Expert Academic Advisor. Goal: Help students plan their degree path and improve performance.",
    "REGISTRATION": "Persona: Registration Officer. Goal: Ensure students follow official dates, credit limits, and steps.",
    "POLICIES": "Persona: Policy Compliance Officer. Goal: Explain university rules, attendance, and integrity standards.",
    "WELLBEING": "Persona: Student Support Specialist. Goal: Provide empathy and stress management resources (non-clinical).",
}

# --- Models ---


@dataclass
class Chunk:
    id: str
    text: str
    title: str


class ChatRequest(BaseModel):
    message: str


# --- RAG Core ---


class RAGEngine:
    def __init__(self, config: Config):
        self.config = config
        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.indexes: Dict[str, Tuple[faiss.Index, List[Dict]]] = {}
        self.init_indexes()

    def init_indexes(self) -> None:
        """Build or load indexes for all KBs."""
        os.makedirs(self.config.INDEX_DIR, exist_ok=True)
        for name, filename in KBS.items():
            kb_path = os.path.join(self.config.DATA_DIR, filename)
            idx_path = os.path.join(self.config.INDEX_DIR, f"{name}.faiss")
            meta_path = os.path.join(self.config.INDEX_DIR, f"{name}.json")

            if os.path.exists(idx_path) and os.path.exists(meta_path):
                print(f"Loading index for {name}...")
                index = faiss.read_index(idx_path)
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                self.indexes[name] = (index, meta)
            elif os.path.exists(kb_path):
                print(f"Building index for {name}...")
                self.build_index(name, kb_path, idx_path, meta_path)
            else:
                print(f"Warning: Knowledge base file {filename} not found.")

    def build_index(self, name, kb_path, idx_path, meta_path) -> None:
        with open(kb_path, "r", encoding="utf-8") as f:
            content = f.read()

        sections = re.split(r"---", content)
        chunks = []
        texts = []
        for i, section in enumerate(sections):
            text = section.strip()
            if len(text) < 50:
                continue

            title_match = re.search(r"title:\s*\"?(.*?)\"?\n", section)
            title = title_match.group(1) if title_match else f"Section {i}"

            clean_text = re.sub(r"---.*?---", "", section, flags=re.DOTALL).strip()
            chunks.append({"id": f"{name}-{i}", "text": clean_text, "title": title})
            texts.append(clean_text)

        if not texts:
            return

        embeddings = self.embed(texts)
        dim = len(embeddings[0])
        index = faiss.IndexFlatIP(dim)

        arr = np.array(embeddings, dtype="float32")
        faiss.normalize_L2(arr)
        index.add(arr)

        faiss.write_index(index, idx_path)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f)

        self.indexes[name] = (index, chunks)

    def embed(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            resp = self.client.embeddings.create(model=self.config.EMBED_MODEL, input=batch)
            all_embeddings.extend([d.embedding for d in resp.data])
        return all_embeddings

    def search(self, query: str, top_k: int = 5) -> Tuple[str, str, List[Dict]]:
        # Expanded keyword routing (same logic as your standalone app)
        q = query.lower()
        reg_keywords = [
            "registration",
            "register",
            "credit hour",
            "credits",
            "passed hours",
            "timeline",
            "schedule",
            "february",
            "spring",
            "semester",
            "enrollment",
            "load",
            "capacity",
            "prerequisite",
            "add",
            "drop",
            "tuition",
            "advisor approval",
            "signature",
            "login",
            "portal",
            "clearance",
        ]
        pol_keywords = [
            "policy",
            "rule",
            "regulation",
            "attendance",
            "grading",
            "grade",
            "exam",
            "final",
            "midterm",
            "quiz",
            "plagiarism",
            "integrity",
            "conduct",
            "misconduct",
            "penalty",
            "late submission",
            "appeal",
            "handbook",
            "official",
            "requirement",
            "eligibility",
            "absence",
        ]
        well_keywords = [
            "stress",
            "burnout",
            "motivation",
            "anxiety",
            "mental health",
            "support",
            "feeling",
            "overwhelmed",
            "lonely",
            "loneliness",
            "depressed",
            "tired",
            "focus",
            "sleep",
            "exercise",
            "routine",
            "balance",
            "struggle",
            "help",
            "counselor",
            "habit",
            "pressure",
            "panic",
        ]
        adv_keywords = [
            "advising",
            "advisor",
            "course planning",
            "major",
            "minor",
            "gpa",
            "improvement",
            "career",
            "internship",
            "resume",
            "cv",
            "graduation",
            "requirements",
            "elective",
            "core",
            "path",
            "goal",
            "success",
            "mentor",
            "feedback",
            "transfer",
            "transcript",
        ]

        kb_name = "ADVISING"
        if any(w in q for w in reg_keywords):
            kb_name = "REGISTRATION"
        elif any(w in q for w in pol_keywords):
            kb_name = "POLICIES"
        elif any(w in q for w in well_keywords):
            kb_name = "WELLBEING"
        elif any(w in q for w in adv_keywords):
            kb_name = "ADVISING"

        if kb_name not in self.indexes:
            return kb_name, "I'm sorry, I don't have access to that information right now.", []

        index, meta = self.indexes[kb_name]
        query_vec = self.embed([query])[0]
        q_arr = np.array([query_vec], dtype="float32")
        faiss.normalize_L2(q_arr)

        scores, indices = index.search(q_arr, top_k)
        hits = [meta[i] for i in indices[0] if 0 <= i < len(meta)]

        context = "\n\n".join([f"[{h['id']}] (Title: {h['title']})\n{h['text']}" for h in hits])

        system_instructions = f"{BASE_PROMPT}\n\n{CATEGORY_PROMPTS.get(kb_name, '')}\n\nCONTEXT:\n{context}"

        resp = self.client.chat.completions.create(
            model=self.config.CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": query},
            ],
        )
        raw = resp.choices[0].message.content
        return kb_name, (raw or "").strip(), hits
