"""Request schemas for the public API.

Mirrors the API contract in project-analysis.md §10.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

SummaryStyle = Literal["simple", "detailed", "bullets"]
Complexity = Literal["beginner", "intermediate", "expert"]
ReadingFrequency = Literal["low", "medium", "high"]

# The five interest categories called out in FR-1.2.
KNOWN_TOPICS = ["politics", "sports", "technology", "finance", "climate"]


class UserPreferences(BaseModel):
    """Session-scoped user preferences (FR-7)."""

    topics: list[str] = Field(
        default_factory=list,
        description="Favorite categories, e.g. ['technology', 'finance'].",
    )
    summary_style: SummaryStyle = Field(
        default="simple",
        description="Preferred summary length/style.",
    )
    complexity: Complexity = Field(
        default="beginner",
        description="Preferred explanation complexity level.",
    )
    reading_frequency: ReadingFrequency = Field(
        default="medium",
        description="How often the user reads news (shapes digest size).",
    )


class ChatRequest(BaseModel):
    """POST /api/chat — a single conversational turn."""

    session_id: str = Field(..., min_length=1, description="Stable per-session id.")
    message: str = Field(..., min_length=1, description="User's chat message.")
    preferences: Optional[UserPreferences] = Field(
        default=None,
        description="Optional preference update sent with this turn.",
    )


class DigestRequest(BaseModel):
    """POST /api/digest — generate a personalized digest (FR-5)."""

    session_id: str = Field(..., min_length=1)
    topics: Optional[list[str]] = Field(
        default=None,
        description="Override topics; if omitted, session favorites are used.",
    )
    style: Optional[SummaryStyle] = Field(
        default=None,
        description="Override summary style; if omitted, session style is used.",
    )


class SimplifyRequest(BaseModel):
    """POST /api/simplify — simplify a topic or article (FR-4 / Route 2)."""

    session_id: str = Field(..., min_length=1)
    content: str = Field(
        default="",
        description="Topic name or raw article text to simplify.",
    )
    url: Optional[str] = Field(
        default=None,
        description="If provided, content is extracted from this URL first.",
    )
    level: Optional[Complexity] = Field(
        default=None,
        description="Output complexity level; if omitted, session complexity is used.",
    )
