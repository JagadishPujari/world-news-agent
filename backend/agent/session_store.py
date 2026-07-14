"""In-memory session store for short-term session memory (FR-7).

Maintains user preferences and chat history isolated per session.
Resets when the backend restarts or session ends.
"""
from __future__ import annotations

from typing import Any, Dict, List, Set
from pydantic import BaseModel

from models.requests import UserPreferences


class SessionState(BaseModel):
    """Container for a single user session's state."""

    session_id: str
    preferences: UserPreferences = UserPreferences()
    viewed_topics: Set[str] = set()
    chat_history: List[Dict[str, str]] = []  # List of {"role": "user"|"assistant", "content": "..."}

    model_config = {
        "arbitrary_types_allowed": True
    }


class SessionStore:
    """Thread-safe (simple dict) in-memory storage for active sessions."""

    def __init__(self) -> None:
        self._sessions: Dict[str, SessionState] = {}

    def get_or_create(self, session_id: str) -> SessionState:
        """Retrieve the state for session_id, creating it if it doesn't exist."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]

    def update_preferences(self, session_id: str, new_prefs: UserPreferences) -> SessionState:
        """Update preferences for the given session."""
        state = self.get_or_create(session_id)
        state.preferences = new_prefs
        return state

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Record a chat message in the session history."""
        state = self.get_or_create(session_id)
        state.chat_history.append({"role": role, "content": content})

    def record_viewed_topic(self, session_id: str, topic: str) -> None:
        """Record a topic category explored during this session."""
        state = self.get_or_create(session_id)
        state.viewed_topics.add(topic.lower())

    def clear(self, session_id: str) -> None:
        """End the session and wipe its memory (FR-7.5)."""
        if session_id in self._sessions:
            del self._sessions[session_id]


# Singleton instance
session_store = SessionStore()
