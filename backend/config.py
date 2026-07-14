"""Centralized configuration loaded from environment variables.

All secrets and tunables are sourced from the environment via python-dotenv /
pydantic-settings. Nothing is hard-coded. See `.env.example` for the full list.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Field names map case-insensitively to the environment variable names
    documented in `.env.example`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Gemini ───────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model_name: str = "gemini-2.5-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com"

    # ── Langfuse ─────────────────────────────────────────────
    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # ── News providers ───────────────────────────────────────
    newsdata_api_key: str = ""
    currents_api_key: str = ""
    news_provider: Literal["newsdata", "currents"] = "newsdata"

    # ── Behaviour toggles ────────────────────────────────────
    frontend_origin: str = "http://localhost:5173"

    # ── Derived helpers ──────────────────────────────────────
    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_secret_key and self.langfuse_public_key)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()
