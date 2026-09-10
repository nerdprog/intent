"""Deterministic Aptitude answer evaluation — LLM never decides correctness."""

from typing import Any, Dict, Optional


def evaluate_answer(
    student_answer: str,
    correct_answer: str,
    topic: str = "",
    question_text: str = "",
) -> Dict[str, Any]:
    submitted = (student_answer or "").strip().upper()
    expected = (correct_answer or "").strip().upper()
    # Allow "B" or "B. 36" style answers
    if submitted and submitted[0] in "ABCD" and (len(submitted) == 1 or not submitted[1].isalpha()):
        submitted = submitted[0]
    if expected and expected[0] in "ABCD":
        expected = expected[0]

    is_correct = bool(submitted) and submitted == expected
    if is_correct:
        feedback = f"Correct. You selected {submitted}."
    else:
        feedback = f"Incorrect. You selected {submitted or 'nothing'}; the correct option is {expected}."

    return {
        "correct": is_correct,
        "topic": topic,
        "submitted_answer": submitted,
        "correct_answer": expected,
        "question_text": question_text,
        "feedback": feedback,
        "delta": 22 if is_correct else -8,
    }
