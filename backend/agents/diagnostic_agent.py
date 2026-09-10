"""Diagnostic Agent — short Aptitude baseline MCQs."""

from typing import Any, Dict, List, Optional

from backend.models.schemas import public_question
from backend.skills.playbooks import diagnose_aptitude_topic
from backend.state import StateManager


def run_diagnostic(student_id: str, topics: Optional[List[str]] = None) -> Dict[str, Any]:
    state = StateManager.get_student_summary(student_id)
    focus = topics or (state.get("weak_topics") or [])
    understand = state.get("understand") or {}
    if not focus:
        focus = (understand.get("topics") or []) or (understand.get("context") or {}).get("weak_topics") or []
    if not focus:
        focus = ["Percentages", "Probability", "Averages"]

    questions = diagnose_aptitude_topic(focus, limit=3)
    first = questions[0]
    rest = questions[1:]
    StateManager.set_diagnostic_queue(student_id, rest)
    StateManager.set_active_question(student_id, first)
    StateManager.update_profile(
        student_id,
        current_topic=first["topic"],
        last_action="DIAGNOSE",
        phase="DIAGNOSE",
    )

    plan_note = ""
    if state.get("days_remaining"):
        plan_note = (
            f" I'll keep your {state.get('days_remaining')} day / "
            f"{(state.get('daily_study_minutes') or 120) // 60}h plan in mind."
        )

    names = ", ".join(q["topic"] for q in questions)
    return {
        "ok": True,
        "action": "DIAGNOSE",
        "topic": first["topic"],
        "response": (
            "I'll start with a **short Aptitude diagnostic** "
            f"({len(questions)} question{'s' if len(questions) != 1 else ''} on {names})."
            f"{plan_note}\n\n"
            "Pick an option and submit — I will score it automatically."
        ),
        "question": public_question(first),
    }
