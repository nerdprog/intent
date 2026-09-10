"""
StudyCrafter — n8n webhook client with local Aptitude orchestrator fallback.
"""

import os
import uuid
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from backend.models.schemas import public_question
from backend.orchestrator import handle_turn
from backend.state import StateManager

load_dotenv()

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "https://nivi0706.app.n8n.cloud/webhook/studycrafter",
)
USE_N8N = os.getenv("USE_N8N", "false").strip().lower() in {"1", "true", "yes"}


class N8NClient:
    """POST /studycrafter when n8n is up; otherwise run local agents."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or N8N_WEBHOOK_URL

    def send_message(
        self,
        student_id: str,
        message: str,
        answer: Optional[str] = None,
        question_id: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Deterministic evaluation always stays local — never an LLM.
        if answer:
            return handle_turn(student_id, message=message or "", answer=answer)

        summary = StateManager.get_student_summary(student_id)
        payload = {
            "student_id": student_id,
            "message": (message or "").strip(),
            "topic": topic or summary.get("current_topic"),
            "mastery": None,
        }

        if not USE_N8N:
            return handle_turn(student_id, message=message or "", answer=None)

        try:
            resp = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=8,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    return self._process_n8n_response(student_id, data, payload)
        except Exception:
            pass

        return handle_turn(student_id, message=message or "", answer=None)

    def _process_n8n_response(
        self, student_id: str, data: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        action = (data.get("action") or "TEACH").upper()
        topic = data.get("topic") or payload.get("topic")
        response_text = data.get("response", "")
        agent_out = data.get("agent_output") or {}
        inner_out = agent_out.get("output", agent_out) if isinstance(agent_out, dict) else {}

        state_info = data.get("student_state") or data.get("state") or {}
        if state_info.get("goal") or state_info.get("days_remaining"):
            StateManager.update_profile(
                student_id,
                goal=state_info.get("goal"),
                days_remaining=state_info.get("days_remaining"),
                daily_study_minutes=state_info.get("daily_study_minutes"),
            )

        question_obj = None
        q_src = inner_out if isinstance(inner_out, dict) else {}
        if data.get("question") or q_src.get("question"):
            raw = data.get("question") if isinstance(data.get("question"), dict) else q_src
            if raw.get("text") or raw.get("question"):
                question_obj = {
                    "id": raw.get("id") or f"q_{uuid.uuid4().hex[:6]}",
                    "question": raw.get("question") or raw.get("text"),
                    "options": raw.get("options") or {},
                    "correct_answer": (raw.get("correct_answer") or "B").strip().upper(),
                    "topic": raw.get("topic") or topic,
                    "difficulty": raw.get("difficulty") or "Easy",
                }
                StateManager.set_active_question(student_id, question_obj)

        StateManager.update_profile(
            student_id,
            current_topic=topic,
            last_action=action,
            phase=action,
        )

        client_q = public_question(question_obj) if question_obj else None
        return {
            "ok": True,
            "action": action,
            "topic": topic,
            "response": response_text,
            "question": client_q,
            "state": data.get("state") or {"mastery": StateManager.get_mastery(student_id, topic)},
            "student_state": StateManager.get_student_summary(student_id),
        }
