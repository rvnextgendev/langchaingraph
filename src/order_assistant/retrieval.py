"""Small, dependency-free lexical retriever over packaged Markdown policies."""

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


def retrieve_policy(question: str, directory: Path = POLICY_DIR) -> tuple[Passage, ...]:
    """Return up to three overlapping-keyword passages; no embeddings/API required."""
    documents = tuple(
        (p.name, p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*.md"))
    )
    query = tokens(question)
    ranked = sorted(
        ((len(query & tokens(p.text)), p) for p in _chunk_documents(documents)),
        key=lambda item: (-item[0], item[1].source),
    )
    return tuple(p for score, p in ranked[:3] if score > 0)
