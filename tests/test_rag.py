"""
Comprehensive test suite for StudyCrafter RAG knowledge base, vector store, and FastAPI endpoints.
Tests:
  1. Loading .txt files
  2. Automatic discovery of all files in /data
  3. Topic extraction
  4. Chunking
  5. Chunk metadata
  6. Embedding/index creation
  7. Semantic retrieval
  8. Topic filtering
  9. top_k parameter
  10. No-result handling
  11. Missing vector-store handling
  12. POST /rag/retrieve endpoint
  13. GET /health endpoint
"""

import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.rag.ingestion import (
    chunk_document,
    discover_txt_files,
    extract_topic_from_filename,
    ingest_aptitude_corpus,
    rebuild_vector_index,
)
from backend.rag.vector_store import VectorStore
from backend.rag_api import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Loading .txt files & 2. Automatic discovery
# ---------------------------------------------------------------------------
def test_discover_txt_files():
    files = discover_txt_files()
    assert len(files) >= 7, f"Expected at least 7 aptitude files, found {len(files)}"
    filenames = [f.name.lower() for f in files]
    assert "averages.txt" in filenames or "average.txt" in filenames
    assert "percentages.txt" in filenames or "percentage.txt" in filenames
    assert "probability.txt" in filenames


# ---------------------------------------------------------------------------
# 3. Topic extraction
# ---------------------------------------------------------------------------
def test_topic_extraction():
    lbl, slug = extract_topic_from_filename(Path("averages.txt"))
    assert lbl == "Averages"
    assert slug == "averages"

    lbl, slug = extract_topic_from_filename(Path("profit_loss.txt"))
    assert lbl == "Profit and Loss"
    assert slug == "profit_and_loss"

    # Test dynamic unmapped filename
    lbl, slug = extract_topic_from_filename(Path("simple_interest.txt"))
    assert lbl == "Simple Interest"
    assert slug == "simple_interest"


# ---------------------------------------------------------------------------
# 4. Chunking & 5. Chunk metadata
# ---------------------------------------------------------------------------
def test_chunking_and_metadata():
    sample_text = """
Concept: Average is sum divided by count.
Formula: Average = Sum / N.

Worked Example:
Question: Find average of 10 and 20.
Answer: (10 + 20) / 2 = 15.

Practice:
Q1: Average of 5, 15, 25 is?
"""
    file_path = Path("c:/Users/mail4/Studycrafter/data/aptitude_knowledge/averages.txt")
    chunks = chunk_document(sample_text, file_path)

    assert len(chunks) >= 3, "Expected at least 3 chunks (concept, example, practice)"
    
    # Verify metadata fields on every chunk
    for chunk in chunks:
        assert "text" in chunk
        meta = chunk["metadata"]
        assert meta["topic"] == "averages"
        assert meta["topic_label"] == "Averages"
        assert "source_file" in meta
        assert "section" in meta
        assert "chunk_id" in meta


# ---------------------------------------------------------------------------
# 6. Embedding / Index creation & 7. Semantic retrieval
# ---------------------------------------------------------------------------
def test_index_creation_and_retrieval(tmp_path):
    # Use temporary vector store path
    vs = VectorStore(persist_directory=tmp_path)
    vs.reset_collection()

    test_chunks = [
        {
            "text": "The formula for Average is Sum of all observations divided by Number of observations.",
            "metadata": {
                "topic": "averages",
                "topic_label": "Averages",
                "section": "concept",
                "source_file": "data/aptitude_knowledge/averages.txt",
                "chunk_id": "test_avg_1",
            },
        },
        {
            "text": "Probability of an event P(E) is Number of favorable outcomes / Total outcomes.",
            "metadata": {
                "topic": "probability",
                "topic_label": "Probability",
                "section": "concept",
                "source_file": "data/aptitude_knowledge/probability.txt",
                "chunk_id": "test_prob_1",
            },
        },
    ]

    vs.add_chunks(test_chunks)
    assert vs.is_available()

    # Semantic search query
    results = vs.search(query="formula for average", top_k=5)
    assert len(results) > 0
    assert "Average" in results[0]["content"] or "Sum" in results[0]["content"]


# ---------------------------------------------------------------------------
# 8. Topic filtering
# ---------------------------------------------------------------------------
def test_topic_filtering(tmp_path):
    vs = VectorStore(persist_directory=tmp_path)
    vs.reset_collection()

    test_chunks = [
        {
            "text": "Average formula: Sum / N",
            "metadata": {
                "topic": "averages",
                "topic_label": "Averages",
                "section": "concept",
                "source_file": "data/aptitude_knowledge/averages.txt",
                "chunk_id": "avg_chunk",
            },
        },
        {
            "text": "Percentage formula: (Value / Total) * 100",
            "metadata": {
                "topic": "percentages",
                "topic_label": "Percentages",
                "section": "concept",
                "source_file": "data/aptitude_knowledge/percentages.txt",
                "chunk_id": "pct_chunk",
            },
        },
    ]
    vs.add_chunks(test_chunks)

    # Filter for Percentages
    results = vs.search(query="formula", topic="Percentages", top_k=2)
    assert len(results) > 0
    assert results[0]["topic"] in ("Percentages", "percentages")
    assert "Percentage" in results[0]["content"]


# ---------------------------------------------------------------------------
# 9. top_k parameter
# ---------------------------------------------------------------------------
def test_top_k_parameter(tmp_path):
    vs = VectorStore(persist_directory=tmp_path)
    vs.reset_collection()

    test_chunks = [
        {
            "text": f"Chunk number {i} regarding math aptitude topics",
            "metadata": {
                "topic": "averages",
                "topic_label": "Averages",
                "section": "general",
                "source_file": "data/test.txt",
                "chunk_id": f"chunk_{i}",
            },
        }
        for i in range(10)
    ]
    vs.add_chunks(test_chunks)

    results = vs.search(query="math aptitude", top_k=3)
    assert len(results) == 3


# ---------------------------------------------------------------------------
# 10. No-result handling
# ---------------------------------------------------------------------------
def test_no_result_handling(tmp_path):
    vs = VectorStore(persist_directory=tmp_path)
    vs.reset_collection()

    # Empty search query on empty store
    results = vs.search(query="", topic=None, top_k=5)
    assert results == []


# ---------------------------------------------------------------------------
# 11. Missing vector-store handling
# ---------------------------------------------------------------------------
def test_missing_vector_store_handling(tmp_path):
    non_existent_dir = tmp_path / "non_existent_vs"
    vs = VectorStore(persist_directory=non_existent_dir)
    assert not vs.is_available()

    with pytest.raises(RuntimeError):
        vs.search(query="test query")


# ---------------------------------------------------------------------------
# 12. POST /rag/retrieve endpoint
# ---------------------------------------------------------------------------
def test_post_rag_retrieve_endpoint():
    # Ensure standard index is built
    rebuild_vector_index()

    payload = {
        "query": "What is the formula for probability?",
        "topic": "Probability",
        "top_k": 3,
    }
    response = client.post("/rag/retrieve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["topic"] == "Probability"
    assert len(data["results"]) > 0
    first = data["results"][0]
    assert "content" in first
    assert "source" in first
    assert "section" in first
    assert "score" in first
    assert first["score"] >= 0.0


# ---------------------------------------------------------------------------
# 13. GET /health endpoint
# ---------------------------------------------------------------------------
def test_get_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "vector_store" in data
    assert data["vector_store"] in ("available", "unavailable")
