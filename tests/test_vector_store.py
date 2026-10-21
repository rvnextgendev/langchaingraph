from pathlib import Path

import pytest

pytest.importorskip("chromadb")

from order_assistant.retrieval import retrieve_policy  # noqa: E402
from order_assistant.vector_store import PolicyVectorIndex  # noqa: E402


class TestEmbedder:
    """Tiny deterministic embedding for storage tests; not a semantic model."""

    __test__ = False

    def __init__(self):
        self.calls = []

    def __call__(self, texts):
        self.calls.append(list(texts))
        return [[1.0, 0.0] if "return" in text.lower() else [0.0, 1.0] for text in texts]


def test_index_persists_embeddings_and_reuses_them(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "returns.md").write_text("Returns accepted for 30 days.", encoding="utf-8")
    embedder = TestEmbedder()
    index = PolicyVectorIndex(docs, tmp_path / "db", embedder)
    assert index.sync() == 1
    assert index.collection.get(include=["embeddings"])["embeddings"].shape == (1, 2)
    assert index.sync() == 1
    assert len(embedder.calls) == 1  # Unchanged documents were not embedded again.

    reopened_embedder = TestEmbedder()
    reopened = PolicyVectorIndex(docs, tmp_path / "db", reopened_embedder)
    matches = reopened.search("return something", max_distance=0.1)
    assert matches[0].source.startswith("returns.md")
    assert reopened_embedder.calls == [["return something"]]  # Only query embedding.
    assert (tmp_path / "db" / "chroma.sqlite3").exists()


def test_updates_and_deletions_remove_stale_vectors(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    policy = docs / "returns.md"
    policy.write_text("Returns accepted for 10 days.", encoding="utf-8")
    index = PolicyVectorIndex(docs, tmp_path / "db", TestEmbedder())
    index.sync()
    policy.write_text("Returns accepted for 20 days.", encoding="utf-8")
    assert index.sync() == 1
    records = index.collection.get(include=["documents"])
    assert records["documents"] == ["Returns accepted for 20 days."]
    policy.unlink()
    assert index.search("returns") == ()
    assert index.collection.count() == 0


def test_distance_cutoff_filters_irrelevant_results(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "returns.md").write_text("Returns accepted.", encoding="utf-8")
    index = PolicyVectorIndex(docs, tmp_path / "db", TestEmbedder())
    assert index.search("astrophysics", max_distance=0.1) == ()


def test_default_retriever_routes_to_vector_index(monkeypatch):
    from unittest.mock import Mock, patch

    monkeypatch.setenv("RAG_BACKEND", "vector")
    monkeypatch.setenv("RAG_MAX_DISTANCE", "0.4")
    index = Mock()
    index.search.return_value = ()
    with patch("order_assistant.vector_store.get_policy_index", return_value=index):
        assert retrieve_policy("policy question", Path("docs")) == ()
    index.search.assert_called_once_with("policy question", max_distance=0.4)


@pytest.mark.parametrize("value", ["bad", "nan", "-1", "3"])
def test_invalid_distance_rejected(monkeypatch, value):
    monkeypatch.setenv("RAG_BACKEND", "vector")
    monkeypatch.setenv("RAG_MAX_DISTANCE", value)
    with pytest.raises(ValueError, match="RAG_MAX_DISTANCE"):
        retrieve_policy("returns")
