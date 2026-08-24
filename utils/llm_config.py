"""LLM provider configuration for StudyCrafter."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ProviderInfo:
    """Metadata for a supported LLM provider."""

    name: str
    env_key: str
    model_env: str
    default_model: str
    base_url: str | None
    signup_url: str
    note: str


# Supported providers — Groq is the recommended free option (no payment method)
PROVIDERS: dict[str, ProviderInfo] = {
    "groq": ProviderInfo(
        name="Groq",
        env_key="GROQ_API_KEY",
        model_env="GROQ_MODEL",
        default_model="llama-3.3-70b-versatile",
        base_url="https://api.groq.com/openai/v1",
        signup_url="https://console.groq.com/keys",
        note="Free tier — no payment method required",
    ),
    "gemini": ProviderInfo(
        name="Google Gemini",
        env_key="GEMINI_API_KEY",
        model_env="GEMINI_MODEL",
        default_model="gemini-3.6-flash",
        base_url=None,
        signup_url="https://aistudio.google.com/apikey",
        note="Free tier — no payment method required",
    ),
    "openai": ProviderInfo(
        name="OpenAI",
        env_key="OPENAI_API_KEY",
        model_env="OPENAI_MODEL",
        default_model="gpt-4o-mini",
        base_url=None,
        signup_url="https://platform.openai.com/api-keys",
        note="Requires billing / credits on your OpenAI account",
    ),
}


def get_active_provider() -> str:
    """Return the configured provider name (defaults to groq)."""
    provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    if provider not in PROVIDERS:
        return "groq"
    return provider


def get_llm_settings() -> tuple[str, ProviderInfo, str, str]:
    """
    Load provider settings from environment.

    Returns:
        Tuple of (provider_id, provider_info, api_key, model_name).
    """
    provider_id = get_active_provider()
    info = PROVIDERS[provider_id]
    api_key = os.getenv(info.env_key, "").strip()
    model = os.getenv(info.model_env, info.default_model).strip() or info.default_model
    return provider_id, info, api_key, model
