"""
Vector Store wrapper for StudyCrafter RAG.
Supports persistent vector embeddings using ChromaDB, with a lightweight 
scikit-learn TF-IDF + Cosine Similarity persistent vector store fallback 
for cloud environments with memory limits (e.g. Render 512MB RAM).
"""

import json
import os
from pathlib import Path
import pickle
from typing import Any, Dict, List, Optional

DEFAULT_VECTOR_STORE_DIR = (
    Path(__file__).resolve().parent.parent.parent / "data" / "vector_store"
)

COLLECTION_NAME = "study_crafter_rag"


def get_vector_store_dir() -> Path:
    env_path = os.environ.get("VECTOR_STORE_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_VECTOR_STORE_DIR


class VectorStore:
    def __init__(self, persist_directory: Optional[Path] = None):
        self.persist_directory = persist_directory or get_vector_store_dir()
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self._backend = None
        self._chroma_client = None
        self._fallback_index = None

    def _init_backend(self):
        if self._backend is not None:
            return

        # Check FORCE_VECTOR_BACKEND env var or attempt ChromaDB first
        pref = os.environ.get("VECTOR_BACKEND", "").lower()
        if pref == "fallback" or pref == "tfidf":
            self._backend = "fallback"
            return

        try:
            import chromadb

            self._chroma_client = chromadb.PersistentClient(path=str(self.persist_directory))
            self._backend = "chroma"
        except Exception as e:
            print(f"ChromaDB not available ({e}), using Persistent TF-IDF Vector Store.")
            self._backend = "fallback"

    def is_available(self) -> bool:
        """Check if vector store index exists and contains indexed chunks."""
        self._init_backend()
        if self._backend == "chroma":
            try:
                coll = self._chroma_client.get_collection(COLLECTION_NAME)
                return coll.count() > 0
            except Exception:
                return False
        else:
            index_path = self.persist_directory / "tfidf_index.pkl"
            return index_path.exists()

    def reset_collection(self):
        """Reset index for clean rebuild."""
        self._init_backend()
        if self._backend == "chroma":
            try:
                self._chroma_client.delete_collection(COLLECTION_NAME)
            except Exception:
                pass
            return self._chroma_client.get_or_create_collection(COLLECTION_NAME)
        else:
            index_path = self.persist_directory / "tfidf_index.pkl"
            if index_path.exists():
                index_path.unlink()
            self._fallback_index = None

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Add list of chunk dicts into persistent vector store."""
        if not chunks:
            return

        self._init_backend()
        if self._backend == "chroma":
            coll = self._chroma_client.get_or_create_collection(COLLECTION_NAME)
            ids = [c["metadata"]["chunk_id"] for c in chunks]
            documents = [c["text"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]
            coll.upsert(ids=ids, documents=documents, metadatas=metadatas)
        else:
            # Build scikit-learn TF-IDF persistent vector index
            from sklearn.feature_extraction.text import TfidfVectorizer
            import numpy as np

            documents = [c["text"] for c in chunks]
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            matrix = vectorizer.fit_transform(documents)

            index_data = {
                "vectorizer": vectorizer,
                "matrix": matrix,
                "chunks": chunks,
            }
            index_path = self.persist_directory / "tfidf_index.pkl"
            with open(index_path, "wb") as f:
                pickle.dump(index_data, f)
            self._fallback_index = index_data

    def _load_fallback_index(self):
        if self._fallback_index is not None:
            return self._fallback_index

        index_path = self.persist_directory / "tfidf_index.pkl"
        if not index_path.exists():
            return None

        with open(index_path, "rb") as f:
            self._fallback_index = pickle.load(f)
        return self._fallback_index

    def search(
        self,
        query: str,
        topic: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search with optional topic filtering.
        Returns list of result dicts with content, source, section, score.
        """
        if not query or not query.strip():
            if topic:
                return self._get_topic_chunks(topic, top_k=top_k)
            return []

        if not self.is_available():
            raise RuntimeError("Vector store is unavailable or not indexed.")

        self._init_backend()

        if self._backend == "chroma":
            return self._search_chroma(query=query, topic=topic, top_k=top_k)
        else:
            return self._search_fallback(query=query, topic=topic, top_k=top_k)

    def _search_chroma(
        self, query: str, topic: Optional[str] = None, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        coll = self._chroma_client.get_collection(COLLECTION_NAME)
        total_count = coll.count()
        if total_count == 0:
            return []

        n_results = min(top_k * 3, total_count)
        where_clause = None
        if topic and topic.strip():
            t_str = topic.strip()
            where_clause = {"$or": [{"topic": t_str}, {"topic_label": t_str}]}

        query_kwargs = {"query_texts": [query.strip()], "n_results": n_results}
        try:
            if where_clause:
                query_kwargs["where"] = where_clause
            results = coll.query(**query_kwargs)
        except Exception:
            query_kwargs.pop("where", None)
            results = coll.query(**query_kwargs)

        output = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

            for doc, meta, dist in zip(docs, metas, distances):
                score = round(max(0.0, 1.0 - (dist / 2.0)), 4)
                if topic and topic.strip():
                    t_clean = topic.strip().lower()
                    m_topic = str(meta.get("topic", "")).lower()
                    m_label = str(meta.get("topic_label", "")).lower()
                    if t_clean in m_topic or t_clean in m_label or m_topic in t_clean or m_label in t_clean:
                        score = min(1.0, score + 0.1)

                output.append({
                    "content": doc,
                    "source": meta.get("source_file") or meta.get("source", "knowledge_base"),
                    "section": meta.get("section", "general"),
                    "score": score,
                    "topic": meta.get("topic_label") or meta.get("topic"),
                })

            output.sort(key=lambda x: x["score"], reverse=True)
            if topic and topic.strip():
                t_clean = topic.strip().lower()
                matching = [item for item in output if t_clean in str(item.get("topic", "")).lower()]
                if matching:
                    output = matching + [item for item in output if item not in matching]

            output = output[:top_k]

        return output

    def _search_fallback(
        self, query: str, topic: Optional[str] = None, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        index_data = self._load_fallback_index()
        if not index_data:
            return []

        vectorizer = index_data["vectorizer"]
        matrix = index_data["matrix"]
        chunks = index_data["chunks"]

        query_vec = vectorizer.transform([query.strip()])
        sims = cosine_similarity(query_vec, matrix)[0]

        results = []
        t_clean = topic.strip().lower() if topic and topic.strip() else None

        for idx, score in enumerate(sims):
            chunk = chunks[idx]
            meta = chunk["metadata"]
            m_topic = str(meta.get("topic", "")).lower()
            m_label = str(meta.get("topic_label", "")).lower()

            final_score = float(score)

            # Topic matching boost
            is_topic_match = False
            if t_clean:
                if t_clean in m_topic or t_clean in m_label or m_topic in t_clean or m_label in t_clean:
                    is_topic_match = True
                    final_score += 0.2

            if final_score > 0 or is_topic_match:
                results.append({
                    "content": chunk["text"],
                    "source": meta.get("source_file") or meta.get("source", "knowledge_base"),
                    "section": meta.get("section", "general"),
                    "score": round(min(1.0, max(0.0, final_score)), 4),
                    "topic": meta.get("topic_label") or meta.get("topic"),
                    "is_topic_match": is_topic_match,
                })

        # Sort: first by topic match if topic filter provided, then by score
        if t_clean:
            results.sort(key=lambda x: (x["is_topic_match"], x["score"]), reverse=True)
        else:
            results.sort(key=lambda x: x["score"], reverse=True)

        # Remove temporary sorting flag
        for r in results:
            r.pop("is_topic_match", None)

        return results[:top_k]

    def _get_topic_chunks(self, topic: str, top_k: int = 5) -> List[Dict[str, Any]]:
        self._init_backend()
        output = []
        t_clean = topic.strip().lower()

        if self._backend == "chroma":
            coll = self._chroma_client.get_collection(COLLECTION_NAME)
            all_data = coll.get()
            if all_data and all_data.get("documents"):
                docs = all_data["documents"]
                metas = all_data.get("metadatas") or [{}] * len(docs)
                for doc, meta in zip(docs, metas):
                    m_topic = str(meta.get("topic", "")).lower()
                    m_label = str(meta.get("topic_label", "")).lower()
                    if t_clean in m_topic or t_clean in m_label or m_topic in t_clean or m_label in t_clean:
                        output.append({
                            "content": doc,
                            "source": meta.get("source_file") or meta.get("source", "knowledge_base"),
                            "section": meta.get("section", "general"),
                            "score": 1.0,
                            "topic": meta.get("topic_label") or meta.get("topic"),
                        })
        else:
            index_data = self._load_fallback_index()
            if index_data and "chunks" in index_data:
                for chunk in index_data["chunks"]:
                    meta = chunk["metadata"]
                    m_topic = str(meta.get("topic", "")).lower()
                    m_label = str(meta.get("topic_label", "")).lower()
                    if t_clean in m_topic or t_clean in m_label or m_topic in t_clean or m_label in t_clean:
                        output.append({
                            "content": chunk["text"],
                            "source": meta.get("source_file") or meta.get("source", "knowledge_base"),
                            "section": meta.get("section", "general"),
                            "score": 1.0,
                            "topic": meta.get("topic_label") or meta.get("topic"),
                        })

        return output[:top_k]
