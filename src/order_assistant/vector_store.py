"""Local MiniLM embeddings and a persistent Chroma policy collection."""

import hashlib
import os
from functools import lru_cache
from pathlib import Path
from threading import RLock
from typing import Any

from order_assistant.retrieval import POLICY_DIR, Passage, load_passages

DEFAULT_DB_DIR = Path(__file__).resolve().parents[2] / ".data" / "chroma"
INDEX_LOCK = RLock()


class PolicyVectorIndex:
    """One corpus per collection; synchronize content IDs before every query."""

    def __init__(self, directory: Path, db_dir: Path, embedder: Any = None):
        import chromadb
        from chromadb.config import Settings
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        self.directory = directory.resolve()
        self.embedder = embedder if embedder is not None else DefaultEmbeddingFunction()
        self.client = chromadb.PersistentClient(
            path=str(db_dir.resolve()), settings=Settings(anonymized_telemetry=False)
        )
        # Keep the model and chunking version in the name; changing either requires
        # a fresh collection, never a mixture of incompatible embedding spaces.
        corpus = hashlib.sha256(str(self.directory).encode()).hexdigest()[:16]
        self.collection = self.client.get_or_create_collection(
            name=f"policies-minilm-v1-{corpus}",
            embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
            metadata={"embedding_model": "all-MiniLM-L6-v2", "chunk_version": 1},
        )

    def _sync(self) -> int:
        passages = load_passages(self.directory)
        wanted = {
            hashlib.sha256((p.source + "\0" + p.text).encode()).hexdigest(): p for p in passages
        }
        existing = set(self.collection.get(include=[])["ids"])
        new_ids = sorted(wanted.keys() - existing)
        # Persist new embeddings before removing old records. If embedding fails,
        # the call raises and no answer is generated from the outdated collection.
        for start in range(0, len(new_ids), 64):
            ids = new_ids[start : start + 64]
            texts = [wanted[key].text for key in ids]
            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=self.embedder(texts),
                metadatas=[{"source": wanted[key].source} for key in ids],
            )
        stale = sorted(existing - wanted.keys())
        if stale:
            self.collection.delete(ids=stale)
        return len(wanted)

    def sync(self) -> int:
        """Build/update the persistent index without a Groq call."""
        with INDEX_LOCK:
            return self._sync()

    def search(self, question: str, max_distance: float = 0.65) -> tuple[Passage, ...]:
        """Embed the question and return up to three cosine-distance matches."""
        if not question.strip():
            return ()
        with INDEX_LOCK:
            count = self._sync()
            if not count:
                return ()
            result = self.collection.query(
                query_embeddings=self.embedder([question]),
                n_results=min(3, count),
                include=["documents", "metadatas", "distances"],
            )
            return tuple(
                Passage(metadata["source"], document)
                for document, metadata, distance in zip(
                    result["documents"][0],
                    result["metadatas"][0],
                    result["distances"][0],
                    strict=True,
                )
                if distance <= max_distance
            )


@lru_cache(maxsize=4)
def _cached_index(directory: str, db_dir: str) -> PolicyVectorIndex:
    return PolicyVectorIndex(Path(directory), Path(db_dir))


def get_policy_index(directory: Path = POLICY_DIR) -> PolicyVectorIndex:
    db_dir = Path(os.getenv("CHROMA_DB_DIR") or DEFAULT_DB_DIR).expanduser().resolve()
    return _cached_index(str(directory.resolve()), str(db_dir))
