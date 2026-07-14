"""Langfuse observability wiring (FR-9).

Provides:
- A shared Langfuse client (for manual traces / scoring / flushing).
- A per-request CallbackHandler that LangChain uses to automatically capture
  LLM outputs, tool calls, workflow paths, latency, and errors/retries.

Everything degrades gracefully: if Langfuse keys are absent the handler is
`None` and the app runs without tracing (useful for offline/dev runs).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional

from config import get_settings


@lru_cache
def get_langfuse_client():
    """Return a cached Langfuse client, or None if not configured."""
    settings = get_settings()
    if not settings.langfuse_enabled:
        return None
    try:
        from langfuse import Langfuse

        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception:  # pragma: no cover - defensive: never break the app
        return None


def is_langfuse_enabled() -> bool:
    return get_langfuse_client() is not None


def get_langfuse_handler(
    *,
    session_id: str,
    user_id: Optional[str] = None,
    workflow: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> Optional[Any]:
    """Build a LangChain CallbackHandler bound to this request's context.

    The handler is passed into the agent's `config={"callbacks": [...]}` so that
    every LLM call, tool invocation, and chain step is traced under one trace,
    grouped by `session_id` and attributed to `user_id`.

    Returns None when Langfuse is not configured.
    """
    settings = get_settings()
    if not settings.langfuse_enabled:
        return None

    try:
        from langfuse.callback import CallbackHandler

        metadata = {"workflow": workflow} if workflow else {}
        return CallbackHandler(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
            session_id=session_id,
            user_id=user_id,
            tags=tags or [],
            metadata=metadata,
        )
    except Exception:  # pragma: no cover - defensive
        return None


def flush() -> None:
    """Flush pending traces (call on shutdown so nothing is lost)."""
    client = get_langfuse_client()
    if client is not None:
        try:
            client.flush()
        except Exception:  # pragma: no cover
            pass
