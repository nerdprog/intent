"""Tutor Agent — handles LLM calls for StudyCrafter."""

import hashlib
from typing import Optional

from openai import APIConnectionError, AuthenticationError, OpenAI, OpenAIError, RateLimitError

from prompts.tutor_prompt import SYSTEM_PROMPT, build_context_message
from utils.llm_config import PROVIDERS, get_active_provider, get_llm_settings

# Limit history sent to the LLM to keep responses fast
MAX_HISTORY_MESSAGES = 10
MAX_OUTPUT_TOKENS = 1600

# Reuse Gemini model instances across requests (system prompt is static)
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
        """Return a short label for the active provider (for UI display)."""
        provider_id = get_active_provider()
        info = PROVIDERS[provider_id]
        return f"{info.name} ({info.note})"

    @staticmethod
    def _trim_history(chat_history: list) -> list:
        """Keep only recent messages so API calls stay fast."""
        if len(chat_history) <= MAX_HISTORY_MESSAGES:
            return chat_history
        return chat_history[-MAX_HISTORY_MESSAGES:]

    @staticmethod
    def _validate_api_key(api_key: str, provider_id: str) -> None:
        """Raise a clear error if the API key is missing or still a placeholder."""
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
        """Lazy-initialize the OpenAI-compatible client (works for OpenAI and Groq)."""
        if self._client is None:
            self._validate_api_key(self.api_key, self.provider_id)
            kwargs = {"api_key": self.api_key}
            if self.provider_info.base_url:
                kwargs["base_url"] = self.provider_info.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def _build_messages(
        self, student_context: dict, chat_history: list
    ) -> list[dict]:
        """Build the message list for OpenAI-compatible APIs."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "system",
                "content": build_context_message(student_context),
            },
        ]

        for turn in self._trim_history(chat_history):
            messages.append({"role": turn["role"], "content": turn["content"]})

        return messages

    def _generate_openai_compatible(
        self, student_context: dict, chat_history: list, user_message: str
    ) -> str:
        """Call OpenAI or Groq using the shared chat completions API."""
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
        """Map retired Gemini model names to a currently available model."""
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
        """Return a cached Gemini model instance for faster repeat calls."""
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

    def _generate_gemini(
        self, student_context: dict, chat_history: list, user_message: str
    ) -> str:
        """Call Google Gemini API (free tier available)."""
        model_name = self._resolve_gemini_model(self.model)
        model = self._get_gemini_model(model_name)

        # Seed chat with student context once, then replay recent history
        history = [
            {
                "role": "user",
                "parts": [build_context_message(student_context)],
            },
            {
                "role": "model",
                "parts": ["Got it. I'll tailor my tutoring to this student profile."],
            },
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

    def generate_response(
        self, student_context: dict, chat_history: list, user_message: str
    ) -> str:
        """Generate a tutor response for the latest user message."""
        if not user_message or not user_message.strip():
            raise ValueError("Message cannot be empty.")

        if self.provider_id == "gemini":
            return self._generate_gemini(student_context, chat_history, user_message)

        return self._generate_openai_compatible(
            student_context, chat_history, user_message
        )

    @staticmethod
    def format_error(error: Exception) -> str:
        """Return a user-friendly error message for display in the chat UI."""
        # Google Gemini / API Core errors
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
                code = (error_body.get("error") or {}).get("code") or error_body.get(
                    "code"
                )
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

            return (
                "⚠️ **Rate Limit:** Too many requests. Wait a minute and try again."
            )
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
