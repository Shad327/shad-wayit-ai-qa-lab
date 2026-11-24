"""Small lexical retrieval baseline; no model calls or embeddings.

Preserve exact passages, line numbers, and a document hash so a reviewer can
verify every returned claim against the input. Source text is data, never code.
"""

import hashlib
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

STOP_WORDS = set("a an and are as at be by can for from how in is it of on or that the this to what with must should".split())


def tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())) - STOP_WORDS


@dataclass(frozen=True)
class Passage:
    id: str
    section: str
    text: str
    source: str
    version: str
    document_sha256: str
    start_line: int
    end_line: int


def parse_document(text: str, source: str = "requirements.md") -> List[Passage]:
    """Index explicit requirements and nonempty section introductions separately."""
    if not text.strip():
        raise ValueError("Document is empty")
    lines = text.splitlines()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    version_match = re.search(r"\*\*Document version:\*\*\s*(.+)", text)
    version = version_match.group(1).strip() if version_match else "unspecified"
    section = "Preamble"
    identifier = "preamble"
    start = 0
    passages: List[Passage] = []

    def append(end: int) -> None:
        first, last = start, end
        while first < last and not lines[first].strip():
            first += 1
        while last > first and not lines[last - 1].strip():
            last -= 1
        if first < last:
            passages.append(Passage(identifier, section, "\n".join(lines[first:last]),
                                    source, version, digest, first + 1, last))

    for index, line in enumerate(lines):
        heading = re.match(r"^#{1,6}\s+(.+)$", line)
        requirement = re.match(r"^\*\*([A-Z]+-\d+)\*\*\s+", line)
        if heading or requirement:
            append(index)
            if heading:
                section = heading.group(1)
                identifier = "section-" + str(index + 1)
                start = index + 1
            else:
                identifier = requirement.group(1)
                start = index
    append(len(lines))
    ids = [p.id for p in passages]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate requirement identifiers; resolve source ambiguity")
    return passages


def load_document(path: Path) -> List[Passage]:
    if path.stat().st_size > 2_000_000:
        raise ValueError("Document exceeds the 2 MB limit")
    return parse_document(path.read_text(encoding="utf-8"), path.name)


def retrieve(passages: List[Passage], query: str, limit: int = 3) -> dict:
    if not query.strip() or len(query) > 2000:
        raise ValueError("Query must contain 1–2000 characters")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10:
        raise ValueError("Limit must be an integer from 1 to 10")
    terms = tokens(query)
    # Explicit IDs are a precise lookup: never substitute a different requirement.
    ids = set(re.findall(r"\b[A-Z]+-\d+\b", query.upper()))
    content_terms = [tokens(p.text) for p in passages]
    ranked = []
    for passage, words in zip(passages, content_terms):
        if ids:
            score = 1.0 if passage.id.upper() in ids else 0.0
            matched = [passage.id] if score else []
        else:
            matched = sorted(terms & words)
            score = sum(math.log(1 + len(passages) / (1 + sum(t in w for w in content_terms)))
                        for t in matched) / math.sqrt(max(len(words), 1))
        if score > 0:
            ranked.append({**asdict(passage), "score": round(score, 6), "matched_terms": matched})
    ranked.sort(key=lambda item: (-item["score"], item["start_line"]))
    results = ranked[:limit]
    return {"query": query, "method": "lexical_baseline", "status": "matches_found" if results else "no_evidence",
            "results": results, "note": "Scores rank lexical overlap, not confidence or proof of sufficient evidence."}
