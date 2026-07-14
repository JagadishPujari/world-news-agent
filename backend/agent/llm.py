"""Shared Gemini LLM factory.

A single cached ChatGoogleGenerativeAI instance is reused across the agent and
all tools so they share configuration (model name, base URL, API key) sourced
from the environment (FR-8 / env vars table).
"""
from __future__ import annotations

from functools import lru_cache

from config import get_settings


@lru_cache
def get_llm(temperature: float = 0.3):
    """Return a cached Gemini chat model.

    `temperature` is baked into the cache key so callers that need a different
    creativity level (e.g. digest narration vs. factual summary) get distinct
    cached instances.
    """
    settings = get_settings()
    from langchain_google_genai import ChatGoogleGenerativeAI

    kwargs: dict = {
        "model": settings.gemini_model_name,
        "google_api_key": settings.gemini_api_key,
        "temperature": temperature,
        "convert_system_message_to_human": True,
    }

    # Honor a custom base URL when provided (GEMINI_BASE_URL).
    if settings.gemini_base_url:
        kwargs["client_options"] = {"api_endpoint": _strip_scheme(settings.gemini_base_url)}

    return ChatGoogleGenerativeAI(**kwargs)


def _strip_scheme(url: str) -> str:
    """google-generativeai expects a bare host[:port], not a full URL."""
    return url.replace("https://", "").replace("http://", "").rstrip("/")
