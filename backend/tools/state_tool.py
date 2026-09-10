"""get_student_state / update_student_state — MCP-ready memory tools."""

from typing import Any, Dict, Optional

from backend.state import StateManager


def get_student_state(student_id: str) -> Dict[str, Any]:
    return StateManager.get_student_summary(student_id)


def update_student_state(student_id: str, **fields) -> None:
    StateManager.update_profile(student_id, **fields)


def update_mastery(student_id: str, topic: str, new_mastery: int) -> int:
    clamped = max(0, min(100, int(new_mastery)))
    StateManager.update_mastery(student_id, topic, clamped)
    return clamped


def apply_mastery_delta(student_id: str, topic: str, delta: int) -> int:
    return StateManager.apply_mastery_delta(student_id, topic, delta)
