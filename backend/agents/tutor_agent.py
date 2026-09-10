"""Tutor Agent — RAG-grounded interactive Aptitude teaching & direct question answering."""

from typing import Any, Dict, Optional
import logging

from agents.tutor_agent import TutorAgent
from backend.context_builder import build_context
from backend.models.schemas import classify_mastery
from backend.skills.playbooks import explain_aptitude_concept
from backend.state import StateManager

logger = logging.getLogger(__name__)

_tutor_agent: Optional[TutorAgent] = None


def _get_tutor() -> TutorAgent:
    global _tutor_agent
    if _tutor_agent is None:
        _tutor_agent = TutorAgent()
    return _tutor_agent


def run_tutor(student_id: str, topic: str, query: str = "") -> Dict[str, Any]:
    """
    Generate an interactive, context-aware tutor response.
    Directly answers user queries/doubts or provides interactive topic instruction.
    """
    ctx = build_context(student_id, topic=topic, query=query)
    mastery = ctx.get("mastery") or 0
    history_records = StateManager.get_chat_history(student_id)
    
    # Format history for LLM
    chat_history = []
    for m in history_records:
        if m.get("role") in ("user", "assistant"):
            chat_history.append({
                "role": "user" if m["role"] == "user" else "assistant",
                "content": m.get("content", ""),
            })

    student_context = {
        "student_name": ctx.get("student_id", "Student"),
        "goal": ctx.get("goal") or "Aptitude Exam Preparation",
        "days_remaining": int(ctx.get("days_remaining") or 0),
        "daily_hours": float(ctx.get("daily_hours") or 2),
        "current_level": "Advanced" if mastery >= 80 else ("Intermediate" if mastery >= 50 else "Beginner"),
        "current_topic": topic,
        "mastery": mastery,
        "previous_mistakes": ctx.get("previous_mistakes", []),
    }

    effective_query = (query or "").strip()
    if not effective_query:
        effective_query = f"Teach me {topic}"

    response_text = ""
    try:
        tutor = _get_tutor()
        response_text = tutor.generate_response(
            student_context=student_context,
            chat_history=chat_history,
            user_message=effective_query,
        )
    except Exception as exc:
        logger.warning(f"Live LLM call failed in run_tutor: {exc}. Falling back to dynamic RAG lesson.")
        # Graceful fallback: dynamically assemble RAG lesson
        lesson = explain_aptitude_concept(topic, mastery=mastery, query=effective_query)
        if mastery < 50:
            level_note = "We'll start with the **core concept**, a worked step-by-step example, and a key shortcut."
        elif mastery < 80:
            level_note = "You're at **intermediate level** — focusing on formulas, shortcuts, and high-yield problems."
        else:
            level_note = "You're at **advanced level** — focusing on speed techniques and exam edge cases."

        mistakes = ctx.get("previous_mistakes") or []
        mistake_block = ""
        if mistakes:
            mistake_block = "\n\n💡 **Watch out for your earlier mistakes:**\n- " + "\n- ".join(mistakes[:2])

        response_text = (
            f"### 📚 {topic}\n\n"
            f"{level_note}\n\n"
            f"{lesson}"
            f"{mistake_block}\n\n"
            f"👉 *Have a question about this, or ready to try a practice problem? Just ask!*"
        )

    StateManager.update_profile(
        student_id,
        current_topic=topic,
        last_action="TEACH",
        phase="TEACH",
    )

    return {
        "ok": True,
        "action": "TEACH",
        "topic": topic,
        "response": response_text,
        "question": None,
        "state": {"mastery": mastery, "status": classify_mastery(mastery, mastery > 0)},
    }

