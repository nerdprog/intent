"""
FastAPI HTTP Web Service for StudyCrafter RAG API.
Endpoints:
  GET  /health       - Health check endpoint
  POST /rag/retrieve - Semantic RAG context retrieval endpoint
"""

import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.rag.vector_store import VectorStore

app = FastAPI(
    title="StudyCrafter RAG API",
    description="Public HTTPS API for Aptitude RAG Knowledge Retrieval",
    version="1.0.0",
)

# Enable CORS for n8n Cloud and external web applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vs = VectorStore()


class RetrieveRequest(BaseModel):
    query: str = Field(default="", description="Natural language search query")
    topic: Optional[str] = Field(default=None, description="Optional target topic filter")
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of results")


class RetrieveResult(BaseModel):
    content: str
    source: str
    section: str
    score: float


class RetrieveResponse(BaseModel):
    ok: bool
    topic: Optional[str] = None
    results: List[RetrieveResult] = []
    error: Optional[str] = None


@app.get("/health")
def health_check() -> Dict[str, Any]:
    """Health check endpoint indicating API and Vector Store status."""
    is_available = vs.is_available()
    return {
        "status": "ok",
        "vector_store": "available" if is_available else "unavailable",
    }


@app.post("/rag/retrieve", response_model=RetrieveResponse)
def retrieve(req: RetrieveRequest):
    """
    Retrieve relevant aptitude knowledge chunks based on semantic similarity
    and optional topic filtering.
    """
    if not vs.is_available():
        raise HTTPException(
            status_code=status.HTTP_535_SERVICE_UNAVAILABLE if hasattr(status, "HTTP_535_SERVICE_UNAVAILABLE") else 503,
            detail="Vector store unavailable or not indexed. Run 'python -m backend.rag.ingestion' first.",
        )

    try:
        results = vs.search(
            query=req.query,
            topic=req.topic,
            top_k=req.top_k,
        )

        formatted_results = [
            RetrieveResult(
                content=r["content"],
                source=r.get("source", "data/aptitude_knowledge"),
                section=r.get("section", "general"),
                score=r.get("score", 0.0),
            )
            for r in results
        ]

        return RetrieveResponse(
            ok=True,
            topic=req.topic,
            results=formatted_results,
        )
    except Exception as e:
        return RetrieveResponse(
            ok=False,
            topic=req.topic,
            results=[],
            error=str(e),
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
