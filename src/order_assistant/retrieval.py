"""Policy loading, chunking, and configurable vector/keyword retrieval."""

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

POLICY_DIR = Path(__file__).parent / "policies"
STOP_WORDS = set("a an the is are what how can i my do does of to for in on and policy".split())


@dataclass(frozen=True)
class Passage:
    source: str
    text: str


def tokens(text: str) -> set[str]:
    words = set(re.findall(r"[a-z]+", text.lower())) - STOP_WORDS
    return {word[:-1] if word.endswith("s") else word for word in words}


@lru_cache(maxsize=8)
def _chunk_documents(documents: tuple[tuple[str, str], ...]) -> tuple[Passage, ...]:
    """Cache by contents so editing a policy invalidates its previous chunks."""
    passages = []
    for name, text in documents:
        for number, paragraph in enumerate(text.split("\n\n"), start=1):
            if paragraph.strip() and not paragraph.startswith("#"):
                for offset in range(0, len(paragraph), 1200):
                    passages.append(
                        Passage(
                            f"{name}:paragraph-{number}:{offset}",
                            paragraph[offset : offset + 1200].strip(),
                        )
                    )
    return tuple(passages)


def load_passages(directory: Path = POLICY_DIR) -> tuple[Passage, ...]:
    if not directory.is_dir():
        raise ValueError("The policy document directory does not exist.")
    documents = tuple(
        (p.name, p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*.md"))
    )
    return _chunk_documents(documents)


def retrieve_keyword_policy(question: str, directory: Path = POLICY_DIR) -> tuple[Passage, ...]:
    """Return up to three overlapping-keyword passages; no embeddings/API required."""
    query = tokens(question)
    ranked = sorted(
        ((len(query & tokens(p.text)), p) for p in load_passages(directory)),
        key=lambda item: (-item[0], item[1].source),
    )
    return tuple(p for score, p in ranked[:3] if score > 0)


def retrieve_policy(question: str, directory: Path = POLICY_DIR) -> tuple[Passage, ...]:
    """Default to persisted semantic retrieval; keyword is an explicit alternative."""
    from dotenv import load_dotenv

    load_dotenv()
    backend = os.getenv("RAG_BACKEND", "vector").strip().lower()
    if backend == "keyword":
        return retrieve_keyword_policy(question, directory)
    if backend != "vector":
        raise ValueError("RAG_BACKEND must be vector or keyword.")
    from order_assistant.vector_store import get_policy_index

    try:
        max_distance = float(os.getenv("RAG_MAX_DISTANCE", "0.65"))
    except ValueError:
        raise ValueError("RAG_MAX_DISTANCE must be a number between 0 and 2.") from None
    if not 0 <= max_distance <= 2:
        raise ValueError("RAG_MAX_DISTANCE must be between 0 and 2.")
    return get_policy_index(directory).search(question, max_distance=max_distance)
