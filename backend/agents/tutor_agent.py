"""Tutor Agent — RAG-grounded interactive Aptitude teaching & direct question answering."""

import hashlib
import logging
from typing import Any, Dict, Optional

from openai import APIConnectionError, AuthenticationError, OpenAI, OpenAIError, RateLimitError

from backend.context_builder import build_context
from backend.models.schemas import classify_mastery
from backend.skills.playbooks import explain_aptitude_concept
from backend.state import StateManager
from prompts.tutor_prompt import SYSTEM_PROMPT, build_context_message
from utils.llm_config import PROVIDERS, get_active_provider, get_llm_settings

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 10
MAX_OUTPUT_TOKENS = 1600
_GEMINI_MODELS: dict[str, object] = {}
_GEMINI_CONFIGURED = False
_PROMPT_CACHE_KEY = hashlib.md5(SYSTEM_PROMPT.encode()).hexdigest()[:8]


class TutorAgent:
    """AI Aptitude Tutor that generates personalized responses via a configurable LLM."""

    def __init__(self):
        self.provider_id, self.provider_info, self.api_key, self.model = get_llm_settings()
        self._client: Optional[OpenAI] = None

    @staticmethod
    def get_provider_label() -> str:
        provider_id = get_active_provider()
        info = PROVIDERS[provider_id]
        return f"{info.name} ({info.note})"

    @staticmethod
    def _trim_history(chat_history: list) -> list:
        if len(chat_history) <= MAX_HISTORY_MESSAGES:
            return chat_history
        return chat_history[-MAX_HISTORY_MESSAGES:]

    @staticmethod
    def _validate_api_key(api_key: str, provider_id: str) -> None:
        info = PROVIDERS[provider_id]

        if not api_key:
            raise ValueError(
                f"{info.env_key} not found. "
                f"Add a free key to your .env file from {info.signup_url}"
            )

        normalized = api_key.lower()
        placeholder_markers = ("your_", "paste_", "example", "here", "xxx")
        if any(marker in normalized for marker in placeholder_markers):
            raise ValueError(
                f"Your .env file still contains a placeholder {info.env_key}. "
                f"Get a free key from {info.signup_url}"
            )

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._validate_api_key(self.api_key, self.provider_id)
            kwargs = {"api_key": self.api_key}
            if self.provider_info.base_url:
                kwargs["base_url"] = self.provider_info.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def _build_messages(self, student_context: dict, chat_history: list) -> list[dict]:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": build_context_message(student_context)},
        ]

        for turn in self._trim_history(chat_history):
            messages.append({"role": turn["role"], "content": turn["content"]})
        return messages

    def _generate_openai_compatible(self, student_context: dict, chat_history: list, user_message: str) -> str:
        messages = self._build_messages(student_context, chat_history)
        messages.append({"role": "user", "content": user_message.strip()})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=MAX_OUTPUT_TOKENS,
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("The AI returned an empty response. Please try again.")
        return content.strip()

    @staticmethod
    def _resolve_gemini_model(model: str) -> str:
        retired_models = {
            "gemini-2.0-flash",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro",
        }
        if model in retired_models:
            return "gemini-3.6-flash"
        return model

    def _get_gemini_model(self, model_name: str):
        global _GEMINI_CONFIGURED

        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ValueError(
                "Gemini support requires google-generativeai. "
                "Run: pip install google-generativeai"
            ) from exc

        self._validate_api_key(self.api_key, self.provider_id)

        if not _GEMINI_CONFIGURED:
            genai.configure(api_key=self.api_key)
            _GEMINI_CONFIGURED = True

        cache_key = f"{model_name}_{_PROMPT_CACHE_KEY}"
        if cache_key not in _GEMINI_MODELS:
            _GEMINI_MODELS[cache_key] = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=SYSTEM_PROMPT,
            )

        return _GEMINI_MODELS[cache_key]

    def _generate_gemini(self, student_context: dict, chat_history: list, user_message: str) -> str:
        model_name = self._resolve_gemini_model(self.model)
        model = self._get_gemini_model(model_name)

        history = [
            {"role": "user", "parts": [build_context_message(student_context)]},
            {"role": "model", "parts": ["Got it. I'll tailor my tutoring to this student profile."]},
        ]

        for turn in self._trim_history(chat_history):
            content = (turn.get("content") or "").strip()
            if not content:
                continue
            role = "user" if turn.get("role") == "user" else "model"
            history.append({"role": role, "parts": [content]})

        chat = model.start_chat(history=history)
        response = chat.send_message(
            user_message.strip(),
            generation_config={"max_output_tokens": MAX_OUTPUT_TOKENS, "temperature": 0.7},
        )

        if not response.text:
            raise ValueError("The AI returned an empty response. Please try again.")
        return response.text.strip()

    def generate_response(self, student_context: dict, chat_history: list, user_message: str) -> str:
        if not user_message or not user_message.strip():
            raise ValueError("Message cannot be empty.")

        if self.provider_id == "gemini":
            return self._generate_gemini(student_context, chat_history, user_message)

        return self._generate_openai_compatible(student_context, chat_history, user_message)

    @staticmethod
    def format_error(error: Exception) -> str:
        error_module = type(error).__module__
        error_name = type(error).__name__
        if error_module.startswith("google.") or error_name in {
            "NotFound",
            "InvalidArgument",
            "PermissionDenied",
            "ResourceExhausted",
        }:
            message = str(error)
            if "no longer available" in message.lower() or error_name == "NotFound":
                return (
                    "⚠️ **Gemini Model Error:** The configured Gemini model is unavailable. "
                    "Set `GEMINI_MODEL=gemini-3.6-flash` in your `.env` file and restart the app."
                )
            if error_name in {"PermissionDenied", "Unauthenticated"}:
                return (
                    "⚠️ **Invalid Gemini API Key:** Check `GEMINI_API_KEY` in `.env` and "
                    "get a free key from https://aistudio.google.com/apikey"
                )
            if error_name == "ResourceExhausted":
                return (
                    "⚠️ **Gemini Rate Limit:** Free tier limit reached. "
                    "Wait a minute and try again."
                )
            return f"⚠️ **Gemini API Error:** {message}"

        if isinstance(error, ValueError):
            return f"⚠️ **Configuration Error:** {error}"
        if isinstance(error, AuthenticationError):
            provider_id = get_active_provider()
            info = PROVIDERS[provider_id]
            return (
                f"⚠️ **Invalid API Key:** {info.name} rejected your API key. "
                f"Check `{info.env_key}` in `.env` and get a new key from "
                f"{info.signup_url}, then restart the app."
            )
        if isinstance(error, RateLimitError):
            error_body = getattr(error, "body", {}) or {}
            if isinstance(error_body, dict):
                code = (error_body.get("error") or {}).get("code") or error_body.get("code")
            else:
                code = None

            if code == "insufficient_quota":
                return (
                    "⚠️ **No Credits:** Your API key is valid, but this provider "
                    "has no remaining quota. Switch to a free provider in `.env`:\n\n"
                    "`LLM_PROVIDER=groq` with a free key from "
                    "https://console.groq.com/keys\n\n"
                    "Or `LLM_PROVIDER=gemini` with a free key from "
                    "https://aistudio.google.com/apikey"
                )

            return "⚠️ **Rate Limit:** Too many requests. Wait a minute and try again."
        if isinstance(error, APIConnectionError):
            return (
                "⚠️ **Connection Error:** Could not reach the AI service. "
                "Check your internet connection and try again."
            )
        if isinstance(error, OpenAIError):
            return f"⚠️ **API Error:** {error}"
        return (
            "⚠️ **Unexpected Error:** Something went wrong. "
            "Please try again in a moment."
        )


_tutor_agent: Optional[TutorAgent] = None


def _get_tutor() -> TutorAgent:
    global _tutor_agent
    if _tutor_agent is None:
        _tutor_agent = TutorAgent()
    return _tutor_agent


def run_tutor(student_id: str, topic: str, query: str = "") -> Dict[str, Any]:
    ctx = build_context(student_id, topic=topic, query=query)
    mastery = ctx.get("mastery") or 0
    history_records = StateManager.get_chat_history(student_id)

    chat_history = []
    for m in history_records:
        if m.get("role") in ("user", "assistant"):
            chat_history.append({
                "role": "user" if m["role"] == "user" else "assistant",
                "content": m.get("content", ""),
            })

    student_context = {
        "student_name": ctx.get("student_id", "Student"),
        "goal": ctx.get("goal") or "Aptitude Exam Preparation",
        "days_remaining": int(ctx.get("days_remaining") or 0),
        "daily_hours": float(ctx.get("daily_hours") or 2),
        "current_level": "Advanced" if mastery >= 80 else ("Intermediate" if mastery >= 50 else "Beginner"),
        "current_topic": topic,
        "mastery": mastery,
        "previous_mistakes": ctx.get("previous_mistakes", []),
    }

    effective_query = (query or "").strip()
    if not effective_query:
        effective_query = f"Teach me {topic}"

    response_text = ""
    try:
        tutor = _get_tutor()
        response_text = tutor.generate_response(
            student_context=student_context,
            chat_history=chat_history,
            user_message=effective_query,
        )
    except Exception as exc:
        logger.warning(f"Live LLM call failed in run_tutor: {exc}. Falling back to dynamic RAG lesson.")
        lesson = explain_aptitude_concept(topic, mastery=mastery, query=effective_query)
        if mastery < 50:
            level_note = "We'll start with the **core concept**, a worked step-by-step example, and a key shortcut."
        elif mastery < 80:
            level_note = "You're at **intermediate level** — focusing on formulas, shortcuts, and high-yield problems."
        else:
            level_note = "You're at **advanced level** — focusing on speed techniques and exam edge cases."

        mistakes = ctx.get("previous_mistakes") or []
        mistake_block = ""
        if mistakes:
            mistake_block = "\n\n💡 **Watch out for your earlier mistakes:**\n- " + "\n- ".join(mistakes[:2])

        response_text = (
            f"### 📚 {topic}\n\n"
            f"{level_note}\n\n"
            f"{lesson}"
            f"{mistake_block}\n\n"
            f"👉 *Have a question about this, or ready to try a practice problem? Just ask!*"
        )

    StateManager.update_profile(
        student_id,
        current_topic=topic,
        last_action="TEACH",
        phase="TEACH",
    )

    return {
        "ok": True,
        "action": "TEACH",
        "topic": topic,
        "response": response_text,
        "question": None,
        "state": {"mastery": mastery, "status": classify_mastery(mastery, mastery > 0)},
    }

