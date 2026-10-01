"""Tiny offline RAG: BM25 keyword search over local documents, no downloads needed."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TOKEN_RE = re.compile(r"\w+", re.UNICODE)

RAG_SYSTEM_PROMPT = (
    "You are Msaidizi, a helpful assistant for Kenyan users. "
    "Answer ONLY using the context below. If the answer is not in the context, say you don't know. "
    "Cite sources like [1]. Reply in the same language as the question (English or Swahili)."
)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


@dataclass(frozen=True)
class Chunk:
    source: str
    text: str


def load_documents(folder: str | Path, max_chars: int = 800) -> list[Chunk]:
    folder = Path(folder)
    chunks: list[Chunk] = []
    for path in sorted([*folder.glob("*.md"), *folder.glob("*.txt")]):
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")) if p.strip()]
        buffer = ""
        for para in paragraphs:
            if buffer and len(buffer) + len(para) > max_chars:
                chunks.append(Chunk(path.name, buffer))
                buffer = para
            else:
                buffer = f"{buffer}\n\n{para}" if buffer else para
        if buffer:
            chunks.append(Chunk(path.name, buffer))
    return chunks


class BM25Retriever:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.term_freqs = [Counter(tokenize(c.text)) for c in chunks]
        self.lengths = [sum(tf.values()) for tf in self.term_freqs]
        self.avg_len = sum(self.lengths) / len(self.lengths) if chunks else 0.0
        doc_freq = Counter(term for tf in self.term_freqs for term in tf)
        n = len(chunks)
        self.idf = {term: math.log(1 + (n - df + 0.5) / (df + 0.5)) for term, df in doc_freq.items()}

    def search(self, query: str, top_k: int = 3) -> list[tuple[Chunk, float]]:
        terms = tokenize(query)
        scored: list[tuple[Chunk, float]] = []
        for chunk, tf, length in zip(self.chunks, self.term_freqs, self.lengths):
            score = 0.0
            for term in terms:
                freq = tf.get(term, 0)
                if not freq:
                    continue
                norm = freq + self.k1 * (1 - self.b + self.b * length / self.avg_len)
                score += self.idf[term] * freq * (self.k1 + 1) / norm
            if score > 0:
                scored.append((chunk, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]


def build_rag_messages(question: str, hits: list[tuple[Chunk, float]]) -> list[dict[str, str]]:
    context = "\n\n".join(f"[{i}] ({chunk.source})\n{chunk.text}" for i, (chunk, _) in enumerate(hits, 1))
    return [
        {"role": "system", "content": f"{RAG_SYSTEM_PROMPT}\n\nContext:\n{context or 'No relevant context found.'}"},
        {"role": "user", "content": question},
    ]
