"""
StudyCrafter — High-Level Backend API Gateway for Streamlit Frontend
"""

from typing import Any, Dict, Optional
from backend.models.schemas import public_question
from backend.n8n_client import N8NClient
from backend.state import StateManager

_client = N8NClient()


def get_or_create_student_session(student_id: Optional[str] = None) -> Dict[str, Any]:
    """Initialize or load student profile."""
    return StateManager.get_or_create_student(student_id)


def process_student_message(student_id: str, message: str) -> Dict[str, Any]:
    """Process incoming natural language query from student."""
    # Record user message in history
    StateManager.add_chat_message(student_id, role="user", content=message)

    # Route to n8n Webhook / Local Agent Engine
    response = _client.send_message(student_id=student_id, message=message)

    # Record assistant message in history
    q_id = response.get("question", {}).get("id") if response.get("question") else None
    StateManager.add_chat_message(
        student_id=student_id,
        role="assistant",
        content=response.get("response", ""),
        action=response.get("action"),
        topic=response.get("topic"),
        question_id=q_id,
    )

    return response


def submit_student_answer(student_id: str, answer_letter: str, question_id: Optional[str] = None) -> Dict[str, Any]:
    """Submit selected MCQ answer for deterministic evaluation."""
    # Record answer in user chat
    user_text = f"My answer is **{answer_letter}**"
    StateManager.add_chat_message(student_id, role="user", content=user_text)

    # Route evaluation
    response = _client.send_message(
        student_id=student_id,
        message="",
        answer=answer_letter,
        question_id=question_id,
    )

    eval_data = response.get("evaluation") or {}
    is_correct = 1 if eval_data.get("correct") else 0

    # Record grading response in assistant chat
    StateManager.add_chat_message(
        student_id=student_id,
        role="assistant",
        content=response.get("response", ""),
        action="ASSESS",
        topic=response.get("topic"),
        question_id=question_id,
        is_graded=1,
        is_correct=is_correct,
    )

    return response


def get_student_state(student_id: str) -> Dict[str, Any]:
    """Get full state for sidebar dashboard."""
    return StateManager.get_student_summary(student_id)


def get_active_question(student_id: str) -> Optional[Dict[str, Any]]:
    """Get active MCQ if pending (no correct_answer)."""
    q = StateManager.get_active_question(student_id)
    if not q:
        return None
    return public_question(q)


def get_chat_history(student_id: str):
    """Get chat history from database."""
    return StateManager.get_chat_history(student_id)


def clear_student_chat(student_id: str):
    """Clear conversation history."""
    StateManager.clear_chat_history(student_id)
