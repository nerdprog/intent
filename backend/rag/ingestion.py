"""
Aptitude Knowledge Base Ingestion & Vector Index Rebuilder.
Discovers all .txt files in /data, extracts topics, chunks by section/content,
creates embeddings, and persists to ChromaDB vector store.
"""

from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

from backend.models.schemas import DOMAIN, SLUG_TO_TOPIC, TOPIC_SLUGS
from backend.rag.vector_store import VectorStore

ROOT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# Pre-defined topic mappings for known aptitude files
FILENAME_TOPIC_MAP = {
    "averages.txt": ("Averages", "averages"),
    "average.txt": ("Averages", "averages"),
    "percentages.txt": ("Percentages", "percentages"),
    "percentage.txt": ("Percentages", "percentages"),
    "probability.txt": ("Probability", "probability"),
    "profit_loss.txt": ("Profit and Loss", "profit_and_loss"),
    "ratio.txt": ("Ratio and Proportion", "ratio"),
    "time_speed_distance.txt": ("Time Speed and Distance", "time_speed_distance"),
    "time_work.txt": ("Time and Work", "time_and_work"),
}


def discover_txt_files(data_dir: Optional[Path] = None) -> List[Path]:
    """Recursively discover all .txt files inside data directory."""
    base_dir = data_dir or ROOT_DATA_DIR
    if not base_dir.exists():
        return []
    txt_files = sorted(list(base_dir.rglob("*.txt")))
    # Filter out any files inside vector_store directory if placed inside data/
    return [f for f in txt_files if "vector_store" not in f.parts]


def extract_topic_from_filename(file_path: Path) -> Tuple[str, str]:
    """
    Extract (topic_label, topic_slug) from file path.
    Falls back to title-cased filename if not pre-mapped.
    """
    filename = file_path.name.lower()
    if filename in FILENAME_TOPIC_MAP:
        return FILENAME_TOPIC_MAP[filename]

    stem = file_path.stem.lower()

    # Check if stem matches TOPIC_SLUGS or SLUG_TO_TOPIC
    if stem in SLUG_TO_TOPIC:
        return SLUG_TO_TOPIC[stem], stem

    for label, slug in TOPIC_SLUGS.items():
        if stem in (label.lower(), slug.lower()):
            return label, slug

    # Fallback formatting: e.g. "simple_interest" -> ("Simple Interest", "simple_interest")
    words = stem.replace("_", " ").replace("-", " ").split()
    label = " ".join(word.capitalize() for word in words)
    slug = "_".join(words)
    return label, slug


def _split_sections(text: str) -> List[Tuple[str, str]]:
    """
    Split document into section chunks (concept, example, practice, or paragraph blocks).
    Returns list of (section_name, section_text).
    """
    lower = text.lower()
    sections: List[Tuple[str, str]] = []

    # Check for known structural section markers
    has_example = "example" in lower or "worked example" in lower
    has_practice = "practice" in lower

    if has_example or has_practice:
        concept = text
        example = ""
        practice = ""

        # Find example split point
        ex_idx = -1
        for marker in ("worked example", "example:", "examples:"):
            idx = lower.find(marker)
            if idx != -1:
                ex_idx = idx
                break

        if ex_idx != -1:
            concept = text[:ex_idx]
            rest = text[ex_idx:]
            
            # Find practice split point
            pr_idx = rest.lower().find("practice")
            if pr_idx != -1:
                example = rest[:pr_idx]
                practice = rest[pr_idx:]
            else:
                example = rest
        else:
            pr_idx = lower.find("practice")
            if pr_idx != -1:
                concept = text[:pr_idx]
                practice = text[pr_idx:]

        if concept.strip():
            sections.append(("concept", concept.strip()))
        if example.strip():
            sections.append(("example", example.strip()))
        if practice.strip():
            sections.append(("practice", practice.strip()))

    else:
        # Split by Markdown headers (# or ##) or double newlines
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        if len(paragraphs) == 1:
            sections.append(("general", paragraphs[0]))
        else:
            for idx, para in enumerate(paragraphs):
                section_type = "concept" if idx == 0 else f"section_{idx+1}"
                sections.append((section_type, para))

    return sections


def chunk_document(text: str, file_path: Path) -> List[Dict]:
    """Chunk document content and generate metadata for each chunk."""
    topic_label, topic_slug = extract_topic_from_filename(file_path)
    try:
        rel_source = str(file_path.relative_to(ROOT_DATA_DIR.parent))
    except ValueError:
        rel_source = str(file_path)

    sections = _split_sections(text)
    chunks = []

    for idx, (section_name, body) in enumerate(sections):
        if not body.strip():
            continue
        chunk_id = f"{topic_slug}_{section_name}_{idx}"
        chunks.append({
            "text": body.strip(),
            "metadata": {
                "domain": DOMAIN,
                "topic": topic_slug,
                "topic_label": topic_label,
                "section": section_name,
                "source_file": rel_source,
                "source": rel_source,
                "chunk_id": chunk_id,
            },
        })

    return chunks


def ingest_aptitude_corpus(data_dir: Optional[Path] = None) -> List[Dict]:
    """Discover all .txt files, read, chunk, and return tagged chunk list."""
    txt_files = discover_txt_files(data_dir)
    all_chunks: List[Dict] = []

    for file_path in txt_files:
        try:
            content = file_path.read_text(encoding="utf-8")
            if not content.strip():
                continue
            chunks = chunk_document(content, file_path)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

    return all_chunks


def rebuild_vector_index(data_dir: Optional[Path] = None, reset: bool = True) -> int:
    """
    Ingest all data files, build vector embeddings, and save to persistent vector store.
    Returns number of indexed chunks.
    """
    chunks = ingest_aptitude_corpus(data_dir)
    if not chunks:
        print("No text files found to index.")
        return 0

    vs = VectorStore()
    if reset:
        vs.reset_collection()

    vs.add_chunks(chunks)
    print(f"Successfully indexed {len(chunks)} chunks from {len(discover_txt_files(data_dir))} files into vector store.")
    return len(chunks)


if __name__ == "__main__":
    count = rebuild_vector_index()
    print(f"Ingestion complete. Total chunks: {count}")
