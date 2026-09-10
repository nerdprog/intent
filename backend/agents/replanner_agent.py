"""Replanner Agent — adapt the Aptitude study plan from mastery + deadline."""

from typing import Any, Dict, List, Optional

from backend.skills.playbooks import create_aptitude_study_plan, replan_aptitude_schedule
from backend.state import StateManager
import json


def run_plan(student_id: str, weak_topics: Optional[List[str]] = None) -> Dict[str, Any]:
    state = StateManager.get_student_summary(student_id)
    weak = weak_topics or state.get("weak_topics") or []
    understand = state.get("understand") or {}
    ctx_weak = (understand.get("context") or {}).get("weak_topics") or []
    weak = [t for t in (ctx_weak or weak) if t] or ["Percentages", "Probability"]
    days = state.get("days_remaining") or 7
    hours = (state.get("daily_study_minutes") or 120) / 60
    plan = create_aptitude_study_plan(
        days,
        hours,
        weak,
        all_topics=list((state.get("mastery") or {}).keys()),
        mastery=state.get("mastery") or {},
    )
    StateManager.update_profile(
        student_id,
        study_plan_json=json.dumps(plan),
        last_action="PLAN",
        phase="PLAN",
        current_topic=weak[0],
    )
    now = plan.get("now") or {}
    nxt = plan.get("next") or {}
    text = (
        "### Your Aptitude plan\n\n"
        f"**Now:** {now.get('topic')} — {now.get('activity')}\n"
        f"**Next:** {nxt.get('topic')}\n\n"
        "We'll start with a short check on your weakest topics. The sidebar plan "
        "will update after each answer."
    )
    return {
        "ok": True,
        "action": "PLAN",
        "topic": weak[0],
        "response": text,
        "question": None,
        "student_state": StateManager.get_student_summary(student_id),
    }


def refresh_study_plan(student_id: str) -> Dict[str, Any]:
    """Rebuild the plan from current mastery without a chat announcement."""
    plan = replan_aptitude_schedule(student_id)
    now = (plan.get("now") or {}).get("topic")
    StateManager.update_profile(
        student_id,
        study_plan_json=json.dumps(plan),
        current_topic=now or StateManager.get_student_summary(student_id).get("current_topic"),
    )
    return plan


def run_replan(student_id: str) -> Dict[str, Any]:
    plan = refresh_study_plan(student_id)
    StateManager.update_profile(student_id, last_action="REPLAN", phase="REPLAN")
    now = plan.get("now") or {}
    nxt = plan.get("next") or {}
    later = plan.get("later") or []
    text = (
        "### Live Aptitude plan\n\n"
        f"**Now:** {now.get('topic')} ({now.get('mastery', 0)}%) — {now.get('activity')}\n"
        f"**Next:** {nxt.get('topic')} ({nxt.get('mastery', 0)}%)\n"
    )
    if later:
        text += f"**Later:** {', '.join(later)}\n"
    text += "\nSay **explain** for the current topic, or **give me a question** to practice."
    return {
        "ok": True,
        "action": "REPLAN",
        "topic": now.get("topic"),
        "response": text,
        "question": None,
        "student_state": StateManager.get_student_summary(student_id),
    }
