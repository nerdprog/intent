"""Shared Aptitude-only schemas for agents, tools, and frontend payloads."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

DOMAIN = "aptitude"

CORE_TOPICS = [
    "Percentages",
    "Ratio and Proportion",
    "Averages",
    "Time and Work",
    "Time Speed and Distance",
    "Profit and Loss",
    "Probability",
]

TOPIC_SLUGS = {
    "Percentages": "percentages",
    "Ratio and Proportion": "ratio",
    "Averages": "averages",
    "Time and Work": "time_and_work",
    "Time Speed and Distance": "time_speed_distance",
    "Profit and Loss": "profit_and_loss",
    "Probability": "probability",
}

SLUG_TO_TOPIC = {v: k for k, v in TOPIC_SLUGS.items()}

ACTIONS = (
    "PROFILE",
    "DIAGNOSE",
    "PLAN",
    "TEACH",
    "PRACTICE",
    "ASSESS",
    "EVALUATE",
    "PROGRESS",
    "REPLAN",
)

INTENTS = (
    "exam_preparation",
    "learn_topic",
    "practice",
    "assess",
    "diagnostic",
    "progress",
    "replan",
    "greeting",
    "general",
)


def classify_mastery(score: int, assessed: bool = True) -> str:
    if not assessed:
        return "Not assessed"
    if score < 50:
        return "Weak"
    if score < 80:
        return "Developing"
    return "Strong"


def public_question(question: Dict[str, Any]) -> Dict[str, Any]:
    """Frontend-safe question payload — never includes correct_answer."""
    text = question.get("question") or question.get("text", "")
    options = question.get("options") or {}
    return {
        "id": question.get("id"),
        "text": text,
        "question": text,
        "options": options,
        "topic": question.get("topic"),
        "difficulty": question.get("difficulty", "Easy"),
    }


@dataclass
class UnderstandResult:
    domain: str = DOMAIN
    goal: str = "Prepare for aptitude test"
    intent: str = "general"
    topics: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    success_criteria: List[str] = field(default_factory=list)
    decomposition: List[str] = field(
        default_factory=lambda: [
            "diagnose",
            "plan",
            "teach",
            "practice",
            "assess",
            "progress",
            "replan",
        ]
    )
    raw_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SupervisorDecision:
    action: str
    topic: Optional[str] = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
