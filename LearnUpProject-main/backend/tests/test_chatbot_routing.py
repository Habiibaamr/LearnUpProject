import json
from types import SimpleNamespace

import numpy as np

from app.services import chatbot_service


class FakeIndex:
    def __init__(self, scores, indices):
        self.scores = np.array([scores], dtype="float32")
        self.indices = np.array([indices], dtype="int64")

    def search(self, _query, _top_k):
        return self.scores, self.indices


class FakeCompletions:
    def __init__(self, payload):
        self.payload = payload
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        message = SimpleNamespace(content=json.dumps(self.payload))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def make_engine(payload):
    completions = FakeCompletions(payload)
    engine = object.__new__(chatbot_service.RAGEngine)
    engine.config = SimpleNamespace(CHAT_MODEL="gpt-4o-mini")
    engine.client = SimpleNamespace(
        chat=SimpleNamespace(completions=completions),
    )
    engine.embed = lambda _texts: [[1.0, 0.0]]
    engine.indexes = {
        "POLICIES": (
            FakeIndex([0.91, 0.72], [0, 1]),
            [
                {
                    "id": "POLICIES-1",
                    "title": "Attendance Policy",
                    "text": "Students must follow the published attendance policy.",
                },
                {
                    "id": "POLICIES-2",
                    "title": "Appeals",
                    "text": "Academic appeals follow the official appeal process.",
                },
            ],
        ),
    }
    return engine, completions


def test_personal_record_requests_return_sis_not_connected_without_openai():
    engine = object.__new__(chatbot_service.RAGEngine)
    engine.embed = lambda _texts: (_ for _ in ()).throw(
        AssertionError("OpenAI embeddings should not be called for SIS requests")
    )

    kb, answer, sources = engine.search("What is my current GPA?")

    assert kb == "SIS_NOT_CONNECTED"
    assert answer.startswith("SIS_NOT_CONNECTED:")
    assert sources == []


def test_general_gpa_advice_is_not_treated_as_a_private_record_request():
    assert not chatbot_service.is_personal_student_record_query(
        "How can I improve my GPA?"
    )


def test_rag_answer_returns_only_model_selected_sources():
    engine, completions = make_engine(
        {
            "mode": "RAG",
            "answer": "Follow the published attendance policy [POLICIES-1].",
            "used_source_ids": ["POLICIES-1"],
        }
    )

    kb, answer, sources = engine.search("What is the attendance policy?")

    assert kb == "POLICIES"
    assert answer.endswith("[POLICIES-1].")
    assert [source["id"] for source in sources] == ["POLICIES-1"]
    assert completions.last_kwargs["response_format"]["type"] == "json_schema"
    assert completions.last_kwargs["response_format"]["json_schema"]["strict"] is True


def test_general_answer_has_general_kb_and_no_sources():
    engine, _ = make_engine(
        {
            "mode": "GENERAL",
            "answer": "K-means groups data points into K clusters.",
            "used_source_ids": [],
        }
    )

    kb, answer, sources = engine.search("Explain K-means clustering")

    assert kb == "GENERAL"
    assert "K-means" in answer
    assert sources == []
