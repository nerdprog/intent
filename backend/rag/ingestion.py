"""
Load existing Aptitude knowledge files into tagged chunks.
Does not replace the knowledge base — it indexes what is already in data/aptitude_knowledge/.
"""

from pathlib import Path
from typing import Dict, List

from backend.models.schemas import DOMAIN, TOPIC_SLUGS

KB_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "aptitude_knowledge"

TOPIC_FILES = {
    "Percentages": "percentages.txt",
    "Ratio and Proportion": "ratio.txt",
    "Averages": "averages.txt",
    "Time and Work": "time_work.txt",
    "Time Speed and Distance": "time_speed_distance.txt",
    "Profit and Loss": "profit_loss.txt",
    "Probability": "probability.txt",
}


def load_topic_document(topic: str) -> str:
    filename = TOPIC_FILES.get(topic)
    if not filename:
        return ""
    path = KB_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def ingest_aptitude_corpus() -> List[Dict]:
    """Split each topic file into concept / example / practice chunks with metadata."""
    chunks: List[Dict] = []
    for topic, filename in TOPIC_FILES.items():
        text = load_topic_document(topic)
        if not text:
            continue
        slug = TOPIC_SLUGS.get(topic, topic.lower().replace(" ", "_"))
        parts = _split_sections(text)
        for section, body in parts.items():
            if not body.strip():
                continue
            chunks.append(
                {
                    "text": body.strip(),
                    "metadata": {
                        "domain": DOMAIN,
                        "topic": slug,
                        "topic_label": topic,
                        "section": section,
                        "source": f"data/aptitude_knowledge/{filename}",
                    },
                }
            )
    return chunks


def _split_sections(text: str) -> Dict[str, str]:
    lower = text.lower()
    concept = text
    example = ""
    practice = ""

    for marker in ("worked example", "example:"):
        idx = lower.find(marker)
        if idx != -1:
            concept = text[:idx]
            rest = text[idx:]
            pidx = rest.lower().find("practice")
            if pidx != -1:
                example = rest[:pidx]
                practice = rest[pidx:]
            else:
                example = rest
            break

    return {
        "concept": concept.strip() or text.strip(),
        "example": example.strip(),
        "practice": practice.strip(),
    }
