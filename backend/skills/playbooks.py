"""Reusable Aptitude learning skills / playbooks."""

from typing import Any, Dict, List, Optional

from backend.models.schemas import classify_mastery
from backend.tools.aptitude_knowledge_tool import get_topic_lesson_text
from backend.tools.assessment_tool import generate_aptitude_question, generate_diagnostic_set
from backend.tools.evaluation_tool import evaluate_answer
from backend.tools.state_tool import apply_mastery_delta, get_student_state


def explain_aptitude_concept(topic: str, mastery: int = 40, query: str = "") -> str:
    return get_topic_lesson_text(topic=topic, query=query, mastery=mastery)


def diagnose_aptitude_topic(topics: List[str], limit: int = 3) -> List[Dict[str, Any]]:
    return generate_diagnostic_set(topics, limit=limit)


def generate_aptitude_mcq(
    topic: str, difficulty: str = "Easy", student_id: Optional[str] = None
) -> Dict[str, Any]:
    return generate_aptitude_question(topic, difficulty, student_id=student_id)


def evaluate_aptitude_answer(student_answer: str, correct_answer: str, topic: str = "") -> Dict[str, Any]:
    return evaluate_answer(student_answer, correct_answer, topic=topic)


def identify_weak_aptitude_topics(student_id: str) -> List[str]:
    state = get_student_state(student_id)
    return state.get("weak_topics") or []


def generate_aptitude_revision(topic: str, mistakes: List[str]) -> str:
    lesson = explain_aptitude_concept(topic, mastery=40)
    mistake_note = ""
    if mistakes:
        mistake_note = "\n\n**Focus on previous mistakes:**\n- " + "\n- ".join(mistakes[:3])
    return lesson + mistake_note


def create_aptitude_study_plan(
    days: int,
    daily_hours: float,
    weak_topics: List[str],
    all_topics: Optional[List[str]] = None,
    mastery: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Build a live plan: weakest topics first, schedule refreshes with mastery."""
    hours = daily_hours or 2
    days = max(int(days or 7), 1)
    scores = mastery or {}

    ranked = []
    if scores:
        ranked = sorted(scores.items(), key=lambda kv: (kv[1], kv[0]))
        ordered = [t for t, _ in ranked]
    else:
        ordered = list(weak_topics or ["Percentages", "Probability"])

    # Keep stated weak topics at the front when scores are still tied/unmeasured
    if weak_topics:
        front = [t for t in weak_topics if t in ordered]
        rest = [t for t in ordered if t not in front]
        ordered = front + rest

    if all_topics:
        for t in all_topics:
            if t not in ordered:
                ordered.append(t)

    if not ordered:
        ordered = ["Percentages", "Probability"]

    now_topic = ordered[0]
    next_topic = ordered[1] if len(ordered) > 1 else now_topic
    later = ordered[2:6]

    now_score = int(scores.get(now_topic, 0))
    if now_score < 50:
        now_activity = "teach + easy practice"
    elif now_score < 80:
        now_activity = "practice + assess"
    else:
        now_activity = "revision / harder questions"

    schedule = []
    for day in range(1, min(days, 7) + 1):
        focus = ordered[(day - 1) % len(ordered)]
        score = int(scores.get(focus, 0))
        if day == 1:
            activity = now_activity
        elif score < 50:
            activity = "teach + practice"
        elif score < 80:
            activity = "practice + assess"
        else:
            activity = "quick revision"
        schedule.append(
            {
                "day": day,
                "focus": focus,
                "activity": activity,
                "hours": hours,
                "mastery": score,
            }
        )

    return {
        "days_remaining": days,
        "daily_hours": hours,
        "priority_topics": ordered[:4],
        "now": {"topic": now_topic, "activity": now_activity, "mastery": now_score},
        "next": {"topic": next_topic, "mastery": int(scores.get(next_topic, 0))},
        "later": later,
        "schedule": schedule,
        "note": "Plan follows current weak topics and updates after each scored answer.",
    }


def replan_aptitude_schedule(student_id: str) -> Dict[str, Any]:
    state = get_student_state(student_id)
    weak = state.get("weak_topics") or []
    days = state.get("days_remaining") or 7
    mins = state.get("daily_study_minutes") or 120
    plan = create_aptitude_study_plan(
        days,
        mins / 60,
        weak,
        all_topics=list((state.get("mastery") or {}).keys()),
        mastery=state.get("mastery") or {},
    )
    plan["note"] = "Updated from latest mastery."
    return plan
