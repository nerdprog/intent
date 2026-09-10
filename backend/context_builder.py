"""Selective context for the current Aptitude request."""

from typing import Any, Dict, Optional

from backend.state import StateManager
from backend.tools.aptitude_knowledge_tool import retrieve_aptitude_knowledge_tool


def build_context(student_id: str, topic: Optional[str] = None, query: str = "") -> Dict[str, Any]:
    """Only the context the current agent needs — not full chat history."""
    state = StateManager.get_student_summary(student_id)
    current = topic or state.get("current_topic")
    mastery = StateManager.get_mastery(student_id, current) if current else 0
    mistakes = []
    if current:
        mistakes = StateManager.get_recent_mistakes(student_id, topic=current, limit=3)

    rag = []
    if current:
        rag = retrieve_aptitude_knowledge_tool(current, query=query, k=2)

    return {
        "domain": "aptitude",
        "topic": current,
        "mastery": mastery,
        "days_remaining": state.get("days_remaining"),
        "daily_study_minutes": state.get("daily_study_minutes"),
        "goal": state.get("goal"),
        "previous_mistakes": [
            m.get("question_text") for m in mistakes if m.get("question_text")
        ],
        "weak_topics": state.get("weak_topics") or [],
        "rag_chunks": [
            {
                "text": c.get("text", "")[:800],
                "source": (c.get("metadata") or {}).get("source"),
                "topic": (c.get("metadata") or {}).get("topic"),
            }
            for c in rag
        ],
        "phase": state.get("phase") or "NEW",
        "diagnosed": bool(state.get("diagnosed")),
    }
