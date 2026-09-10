"""Understand Agent — extract goal, intent, Aptitude topics, constraints, context."""

import json
import re
from typing import Optional

from backend.models.schemas import CORE_TOPICS, UnderstandResult
from backend.state import StateManager

TOPIC_ALIASES = {
    "percentage": "Percentages",
    "percentages": "Percentages",
    "ratio": "Ratio and Proportion",
    "proportion": "Ratio and Proportion",
    "average": "Averages",
    "averages": "Averages",
    "time and work": "Time and Work",
    "time & work": "Time and Work",
    "work": "Time and Work",
    "speed": "Time Speed and Distance",
    "distance": "Time Speed and Distance",
    "tsd": "Time Speed and Distance",
    "profit": "Profit and Loss",
    "loss": "Profit and Loss",
    "p&l": "Profit and Loss",
    "probability": "Probability",
}


def _extract_topics(text: str) -> list:
    lower = text.lower()
    found = []
    # Longer phrases first
    for alias in sorted(TOPIC_ALIASES, key=len, reverse=True):
        if alias in lower:
            topic = TOPIC_ALIASES[alias]
            if topic not in found:
                found.append(topic)
    for topic in CORE_TOPICS:
        if topic.lower() in lower and topic not in found:
            found.append(topic)
    return found


def _extract_weak_topics(text: str, topics: list) -> list:
    lower = text.lower()
    weak = []
    if any(w in lower for w in ("weak", "struggle", "difficult", "bad at", "poor")):
        weak = list(topics)
    # "weak in percentages and probability"
    match = re.search(r"weak(?:er)?(?:\s+in|\s+at)\s+(.+)", lower)
    if match:
        weak = _extract_topics(match.group(1)) or weak
    return weak


def understand_message(student_id: str, message: str) -> UnderstandResult:
    text = (message or "").strip()
    lower = text.lower()
    has_words = bool(re.search(r"[a-zA-Z]{2,}", text))

    topics = _extract_topics(text) if has_words else []
    weak = _extract_weak_topics(text, topics) if has_words else []

    days = None
    hours = None
    if has_words:
        m_days = re.search(r"(\d+)\s*(?:days?|day)\b", lower)
        if m_days:
            days = int(m_days.group(1))
        if "next week" in lower or "in a week" in lower:
            days = days or 7
        m_hours = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|hour)\b", lower)
        if m_hours:
            hours = float(m_hours.group(1))

    # Detect question/doubt patterns
    is_question = "?" in text or any(
        lower.startswith(q) for q in (
            "why", "how", "what", "can you", "could you", "is it", "which", "where", "when", "calculate", "solve", "find", "explain"
        )
    )
    is_hint_request = any(w in lower for w in ("hint", "clue", "stuck", "don't know", "dont know", "help me start"))
    is_practice_request = any(
        phrase in lower for phrase in (
            "give me a question", "give me a practice", "practice question", "practice problem",
            "give question", "another question", "next question", "quiz me", "test me",
            "give me a problem", "new question", "harder question", "easier question",
            "start quiz", "give me mcq", "mcq question"
        )
    ) or (lower in ("practice", "question", "quiz", "problem", "test", "more", "next"))

    intent = "general"
    if not has_words:
        intent = "unclear"
    elif any(w in lower for w in ("diagnostic", "diagnose", "baseline", "take a test", "start test", "assessment test")):
        intent = "diagnostic"
    elif any(w in lower for w in ("progress", "how am i", "my status", "summary", "score", "mastery", "accuracy", "my performance")):
        intent = "progress"
    elif any(w in lower for w in ("replan", "new plan", "update plan", "study plan", "change plan")):
        intent = "replan"
    elif is_hint_request:
        intent = "hint"
    elif is_practice_request:
        intent = "practice"
    elif is_question or any(w in lower for w in ("why", "how to", "what is", "solve", "calculate", "tell me")):
        intent = "ask_question"
    elif any(w in lower for w in ("teach", "explain", "concept", "learn", "lesson", "start", "introduce")):
        intent = "learn_topic"
    elif any(w in lower for w in ("placement", "exam", "aptitude test", "prepare", "days left")):
        intent = "exam_preparation"
    elif not text:
        intent = "greeting"

    goal = "Prepare for aptitude test"
    if "placement" in lower:
        goal = "Campus placement aptitude preparation"
    elif "exam" in lower or "test" in lower:
        goal = "Aptitude test preparation"

    constraints = {}
    if days is not None:
        constraints["days_remaining"] = days
    if hours is not None:
        constraints["daily_hours"] = hours
        constraints["daily_study_minutes"] = int(hours * 60)

    context = {}
    if weak:
        context["weak_topics"] = weak
    if topics:
        context["mentioned_topics"] = topics

    success = [
        "Improve aptitude mastery",
        "Practice weak topics",
        "Achieve target assessment performance",
    ]

    existing = StateManager.get_student_summary(student_id)
    goal_update = None
    if intent == "exam_preparation" or not existing.get("goal"):
        if intent not in ("practice", "progress", "diagnostic"):
            goal_update = goal

    result = UnderstandResult(
        goal=goal,
        intent=intent,
        topics=topics,
        constraints=constraints,
        context=context,
        success_criteria=success,
        raw_message=text,
    )

    # Persist inferred profile without asking the student
    StateManager.update_profile(
        student_id,
        goal=goal_update,
        days_remaining=days,
        daily_study_minutes=int(hours * 60) if hours is not None else None,
        current_topic=(topics[0] if topics else None),
        last_intent=intent,
        understand_json=json.dumps(result.to_dict()),
        phase="UNDERSTAND",
    )
    return result
