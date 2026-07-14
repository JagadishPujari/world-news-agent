"""Response schemas for the public API."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

WorkflowName = Literal[
    "topic_news",
    "url_ingestion",
    "daily_digest",
    "conversation",
]


class NewsItem(BaseModel):
    """A single news article (FR-3.2 fields)."""

    title: str
    description: str = ""
    source: str = ""
    url: str = ""
    published_date: str = ""
    category: str = ""


class ChatResponse(BaseModel):
    """POST /api/chat response."""

    session_id: str
    reply: str
    news_items: list[NewsItem] = Field(default_factory=list)
    workflow_used: WorkflowName = "conversation"
    trace_id: Optional[str] = None


class DigestResponse(BaseModel):
    """POST /api/digest response."""

    session_id: str
    digest: str
    articles_included: int = 0
    topics: list[str] = Field(default_factory=list)
    trace_id: Optional[str] = None


class SimplifyResponse(BaseModel):
    """POST /api/simplify response."""

    session_id: str
    simplified: str
    source_url: Optional[str] = None
    trace_id: Optional[str] = None


class HealthResponse(BaseModel):
    """GET /api/health response."""

    status: str = "ok"
    version: str = "1.0.0"
    auth_enabled: bool = False
    langfuse_enabled: bool = False
    news_provider: str = "newsdata"
