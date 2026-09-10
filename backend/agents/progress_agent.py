"""Progress Agent — deterministic mastery updates after evaluation."""

from typing import Any, Dict

from backend.models.schemas import classify_mastery
from backend.skills.playbooks import evaluate_aptitude_answer
from backend.state import StateManager


def evaluate_and_update(student_id: str, student_answer: str) -> Dict[str, Any]:
    active = StateManager.get_active_question(student_id)
    if not active:
        return {
            "ok": True,
            "action": "ASSESS",
            "topic": None,
            "response": "I don't have an open question to grade. Ask for a practice question first.",
            "question": None,
            "evaluation": {"correct": False},
        }

    topic = active.get("topic") or "Percentages"
    old_mastery = StateManager.get_mastery(student_id, topic)
    result = evaluate_aptitude_answer(
        student_answer=student_answer,
        correct_answer=active.get("correct_answer", ""),
        topic=topic,
    )

    new_mastery = StateManager.apply_mastery_delta(student_id, topic, result["delta"])
    StateManager.mark_question_answered(student_id, result["correct"])

    if not result["correct"]:
        StateManager.add_mistake(
            student_id,
            topic=topic,
            question_text=active.get("question") or "",
            student_answer=result["submitted_answer"],
            correct_answer=result["correct_answer"],
        )

    status = classify_mastery(new_mastery)
    if result["correct"]:
        body = (
            f"✅ **Correct**\n\n{result['feedback']}\n\n"
            f"**{topic} mastery:** {old_mastery}% → **{new_mastery}%** ({status})"
        )
    else:
        body = (
            f"❌ **Incorrect**\n\n{result['feedback']}\n\n"
            f"**{topic} mastery:** {old_mastery}% → **{new_mastery}%** ({status})\n\n"
            "I'll use this mistake the next time we revise this topic."
        )

    StateManager.update_profile(
        student_id,
        current_topic=topic,
        last_action="ASSESS",
        phase="PROGRESS",
    )

    return {
        "ok": True,
        "action": "ASSESS",
        "topic": topic,
        "response": body,
        "question": None,
        "evaluation": {
            "correct": result["correct"],
            "topic": topic,
            "feedback": result["feedback"],
        },
        "state": {
            "mastery": new_mastery,
            "old_mastery": old_mastery,
            "status": status,
        },
        "student_state": StateManager.get_student_summary(student_id),
    }
