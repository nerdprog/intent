"""Assessment Agent — Aptitude MCQs; correct_answer stays backend-only."""

from typing import Any, Dict

from backend.models.schemas import public_question
from backend.skills.playbooks import generate_aptitude_mcq
from backend.state import StateManager


def run_assessment(student_id: str, topic: str, harder: bool = False) -> Dict[str, Any]:
    mastery = StateManager.get_mastery(student_id, topic)
    if harder or mastery >= 80:
        difficulty = "Hard"
    elif mastery >= 50:
        difficulty = "Medium"
    else:
        difficulty = "Easy"

    question = generate_aptitude_mcq(topic, difficulty, student_id=student_id)
    StateManager.set_active_question(student_id, question)
    StateManager.update_profile(
        student_id,
        current_topic=topic,
        last_action="PRACTICE",
        phase="PRACTICE",
    )
    return {
        "ok": True,
        "action": "PRACTICE",
        "topic": topic,
        "response": f"Try this **{difficulty}** Aptitude question on **{topic}**:",
        "question": public_question(question),
        "state": {"mastery": mastery},
    }
