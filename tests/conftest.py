import pytest


@pytest.fixture(autouse=True)
def offline_retrieval(monkeypatch):
    """Workflow/UI tests use deterministic retrieval; vector tests exercise Chroma."""
    monkeypatch.setenv("RAG_BACKEND", "keyword")
