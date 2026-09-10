"""
Local Aptitude orchestrator: Understand → Supervisor → one Act agent → verify → SQLite.
Used when n8n is unavailable, and always for deterministic evaluation.
"""

from typing import Any, Dict, Optional

from backend.agents.assessment_agent import run_assessment
from backend.agents.diagnostic_agent import run_diagnostic
from backend.agents.progress_agent import evaluate_and_update
from backend.agents.replanner_agent import refresh_study_plan, run_plan, run_replan
from backend.agents.supervisor_agent import decide_action
from backend.agents.tutor_agent import run_tutor
from backend.agents.understand_agent import understand_message
from backend.models.schemas import public_question
from backend.state import StateManager


def handle_turn(
    student_id: str,
    message: str = "",
    answer: Optional[str] = None,
) -> Dict[str, Any]:
    StateManager.get_or_create_student(student_id)

    if answer:
        result = evaluate_and_update(student_id, answer)
        refresh_study_plan(student_id)
        nxt = StateManager.pop_diagnostic_question(student_id)
        if nxt:
            StateManager.set_active_question(student_id, nxt)
            result["question"] = public_question(nxt)
            result["response"] += (
                "\n\n**Next diagnostic question** on "
                f"**{nxt.get('topic')}** — select an option below."
            )
            result["action"] = "DIAGNOSE"
        result["student_state"] = StateManager.get_student_summary(student_id)
        return _finalize(student_id, result)

    understand = understand_message(student_id, message)
    decision = decide_action(student_id, understand, has_answer=False)
    topic = decision.topic or (understand.topics[0] if understand.topics else None)
    topic = topic or "Percentages"
    harder = "harder" in (message or "").lower()

    if decision.action == "EVALUATE":
        result = evaluate_and_update(student_id, message)
    elif decision.action == "DIAGNOSE":
        if understand.intent == "exam_preparation" and not StateManager.get_student_summary(student_id).get("study_plan"):
            plan = run_plan(student_id, understand.context.get("weak_topics") or understand.topics)
            diag = run_diagnostic(student_id, understand.topics or understand.context.get("weak_topics"))
            diag["response"] = plan["response"] + "\n\n" + diag["response"]
            result = diag
        else:
            result = run_diagnostic(student_id, understand.topics or understand.context.get("weak_topics"))
    elif decision.action == "PLAN":
        result = run_plan(student_id, understand.topics or understand.context.get("weak_topics"))
    elif decision.action == "TEACH":
        result = run_tutor(student_id, topic, query=message)
    elif decision.action == "PRACTICE":
        result = run_assessment(student_id, topic, harder=harder)
    elif decision.action == "PROGRESS":
        result = _progress_report(student_id, topic)
    elif decision.action == "REPLAN":
        result = run_replan(student_id)
    elif decision.action == "CLARIFY":
        result = _clarify(student_id, understand)
    else:
        result = _welcome_or_profile(student_id, understand)

    result["student_state"] = StateManager.get_student_summary(student_id)
    return _finalize(student_id, result)


def _clarify(student_id: str, understand) -> Dict[str, Any]:
    StateManager.update_profile(student_id, last_action="CLARIFY", phase="UNDERSTAND")
    return {
        "ok": True,
        "action": "CLARIFY",
        "topic": None,
        "response": (
            "I didn't catch a clear request. Try one of these:\n"
            "- **Teach me percentages**\n"
            "- **Give me a practice question**\n"
            "- **Show my progress**"
        ),
        "question": None,
    }


def _welcome_or_profile(student_id: str, understand) -> Dict[str, Any]:
    StateManager.update_profile(student_id, last_action="PROFILE", phase="PROFILE")
    bits = []
    if understand.constraints.get("days_remaining"):
        bits.append(f"{understand.constraints['days_remaining']} days")
    if understand.constraints.get("daily_hours"):
        bits.append(f"{understand.constraints['daily_hours']} hours/day")
    if understand.topics:
        bits.append("topics: " + ", ".join(understand.topics))

    if bits:
        text = (
            "I've saved your Aptitude prep notes ("
            + "; ".join(bits)
            + "). Which topics feel hardest — or say **start diagnostic**."
        )
    else:
        text = (
            "Hi! Tell me about your **aptitude preparation**.\n\n"
            "For example: *I have an aptitude test in 7 days. I can study 2 hours daily "
            "and I am weak in percentages and probability.*"
        )
    return {"ok": True, "action": "PROFILE", "topic": None, "response": text, "question": None}


def _progress_report(student_id: str, topic: str) -> Dict[str, Any]:
    summary = StateManager.get_student_summary(student_id)
    masteries = summary.get("mastery") or {}
    rows = []
    for t, m in masteries.items():
        tag = "Weak" if m < 50 else ("Developing" if m < 80 else "Strong")
        if not (summary.get("questions_attempted") or summary.get("diagnosed")):
            tag = "Not assessed"
        rows.append(f"- **{t}**: `{m}%` — {tag}")
    plan = summary.get("study_plan") or {}
    plan_line = ""
    if plan.get("priority_topics"):
        plan_line = f"\n**Current plan focus:** {', '.join(plan['priority_topics'])}\n"
    text = (
        "### Aptitude progress\n\n"
        f"**Overall:** `{summary.get('overall_mastery', 0)}%` ({summary.get('status')})\n"
        f"**Questions:** {summary.get('questions_correct', 0)} / {summary.get('questions_attempted', 0)} "
        f"(accuracy {summary.get('accuracy', 0)}%)\n"
        f"{plan_line}\n"
        + "\n".join(rows)
    )
    StateManager.update_profile(student_id, last_action="PROGRESS", phase="PROGRESS")
    return {
        "ok": True,
        "action": "PROGRESS",
        "topic": topic,
        "response": text,
        "question": None,
    }


def _finalize(student_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
    if result.get("question") and result["question"].get("correct_answer"):
        result["question"] = public_question(result["question"])
    result.setdefault("ok", True)
    result["student_state"] = result.get("student_state") or StateManager.get_student_summary(student_id)
    return result
