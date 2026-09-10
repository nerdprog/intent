"""Topic-filtered Aptitude RAG retrieval over the existing knowledge files."""

from functools import lru_cache
from typing import List, Optional

from backend.models.schemas import SLUG_TO_TOPIC, TOPIC_SLUGS
from backend.rag.ingestion import ingest_aptitude_corpus, load_topic_document


@lru_cache(maxsize=1)
def _corpus():
    return ingest_aptitude_corpus()


def normalize_topic(topic: Optional[str]) -> Optional[str]:
    if not topic:
        return None
    raw = topic.strip()
    if raw in TOPIC_SLUGS:
        return raw
    slug = raw.lower().replace(" ", "_").replace("-", "_").replace("&", "and")
    if slug in SLUG_TO_TOPIC:
        return SLUG_TO_TOPIC[slug]
    for label in TOPIC_SLUGS:
        if raw.lower() in label.lower() or label.lower() in raw.lower():
            return label
    return raw


def retrieve_aptitude_knowledge(
    topic: str,
    query: str = "",
    section: Optional[str] = None,
    k: int = 3,
) -> List[dict]:
    """
    Retrieve Aptitude chunks for one topic only.
    Authority order: approved local knowledge files (existing RAG corpus).
    """
    label = normalize_topic(topic) or topic
    slug = TOPIC_SLUGS.get(label, label.lower().replace(" ", "_"))
    query_l = (query or "").lower()

    scored = []
    for chunk in _corpus():
        meta = chunk["metadata"]
        if meta.get("domain") != "aptitude":
            continue
        if meta.get("topic") != slug and meta.get("topic_label") != label:
            continue
        if section and meta.get("section") != section:
            continue
        score = 1
        if query_l:
            score += sum(1 for w in query_l.split() if w in chunk["text"].lower())
        if section and meta.get("section") == section:
            score += 2
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [c for _, c in scored[:k]]
    if results:
        return results

    # Fallback: whole topic document
    doc = load_topic_document(label)
    if doc:
        return [
            {
                "text": doc,
                "metadata": {
                    "domain": "aptitude",
                    "topic": slug,
                    "topic_label": label,
                    "section": "full",
                    "source": "aptitude_knowledge",
                },
            }
        ]
    return []


def retrieve_as_text(topic: str, query: str = "", mastery: int = 40) -> str:
    """Build a tutor-ready context string from retrieved chunks."""
    if mastery < 50:
        preferred = ["concept", "example"]
    elif mastery < 80:
        preferred = ["concept", "example", "practice"]
    else:
        preferred = ["example", "practice", "concept"]

    parts = []
    for section in preferred:
        chunks = retrieve_aptitude_knowledge(topic, query=query, section=section, k=1)
        for ch in chunks:
            parts.append(ch["text"])
    if not parts:
        chunks = retrieve_aptitude_knowledge(topic, query=query, k=3)
        parts = [c["text"] for c in chunks]
    return "\n\n".join(parts).strip()
