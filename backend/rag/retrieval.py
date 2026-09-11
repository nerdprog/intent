"""Topic-filtered Aptitude RAG retrieval over the local vector store."""

from typing import List, Optional

from backend.models.schemas import SLUG_TO_TOPIC, TOPIC_SLUGS
from backend.rag.vector_store import VectorStore


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
    topic: Optional[str] = None,
    query: str = "",
    section: Optional[str] = None,
    k: int = 3,
) -> List[dict]:
    """Retrieve relevant chunks from the vector store."""
    label = normalize_topic(topic) or topic
    vs = VectorStore()
    if not vs.is_available():
        return []

    results = vs.search(query=query, topic=label, top_k=k * 2)
    if section:
        results = [r for r in results if r.get("section") == section]

    formatted = []
    for r in results[:k]:
        formatted.append({
            "text": r["content"],
            "metadata": {
                "domain": "aptitude",
                "topic": label,
                "section": r.get("section", "general"),
                "source": r.get("source", ""),
                "score": r.get("score", 0.0),
            },
        })
    return formatted


def retrieve_as_text(topic: str, query: str = "", mastery: int = 40) -> str:
    """Build tutor-ready context, preferring content suited to mastery."""
    if mastery < 50:
        preferred = ["concept", "example"]
    elif mastery < 80:
        preferred = ["concept", "example", "practice"]
    else:
        preferred = ["example", "practice", "concept"]

    parts = []
    for section in preferred:
        chunks = retrieve_aptitude_knowledge(topic, query=query, section=section, k=1)
        parts.extend(chunk["text"] for chunk in chunks)
    if not parts:
        parts = [chunk["text"] for chunk in retrieve_aptitude_knowledge(topic, query=query, k=3)]
    return "\n\n".join(parts).strip()
