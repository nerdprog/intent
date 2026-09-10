"""Supervisor Agent — choose the minimum next Aptitude action."""

from typing import Optional

from backend.models.schemas import SupervisorDecision, UnderstandResult
from backend.state import StateManager


def decide_action(
    student_id: str,
    understand: UnderstandResult,
    has_answer: bool = False,
) -> SupervisorDecision:
    state = StateManager.get_student_summary(student_id)
    topic = None
    if understand.topics:
        topic = understand.topics[0]
    topic = topic or state.get("current_topic")

    if has_answer:
        return SupervisorDecision("EVALUATE", topic, "Student submitted an MCQ answer")

    intent = understand.intent
    diagnosed = bool(state.get("diagnosed"))
    attempted = state.get("questions_attempted") or 0
    mastery = 0
    if topic:
        mastery = (state.get("mastery") or {}).get(topic, 0)

    if intent == "greeting" or intent == "unclear" or not understand.raw_message:
        return SupervisorDecision("CLARIFY", topic, "Empty or unclear message")

    if intent == "diagnostic":
        return SupervisorDecision("DIAGNOSE", topic, "Student requested diagnostic")

    if intent == "progress":
        return SupervisorDecision("PROGRESS", topic, "Student asked for progress")

    if intent == "replan":
        return SupervisorDecision("REPLAN", topic, "Student asked to replan")

    if intent in ("learn_topic", "ask_question", "hint"):
        return SupervisorDecision("TEACH", topic, f"Student query intent: {intent}")

    if intent == "practice":
        return SupervisorDecision("PRACTICE", topic, "Student asked for practice questions")

    if intent == "exam_preparation":
        if attempted == 0 and not diagnosed:
            return SupervisorDecision("DIAGNOSE", topic, "No measured mastery — short diagnostic first")
        if not state.get("study_plan"):
            return SupervisorDecision("PLAN", topic, "Profile known — create study plan")
        if mastery < 50:
            return SupervisorDecision("TEACH", topic, "Weak topic after diagnosis — teach")
        return SupervisorDecision("PRACTICE", topic, "Continue practice on current topic")

    # If the user typed any actual text or question, let the tutor agent respond conversationally
    if understand.raw_message and len(understand.raw_message.strip()) > 3:
        return SupervisorDecision(
            "TEACH",
            topic or "Percentages",
            "Conversational response to student message",
        )

    if topic:
        return SupervisorDecision("TEACH", topic, "Default: teach current Aptitude topic")

    return SupervisorDecision("PROFILE", None, "Need a natural-language goal or topic")
