"""Tools package exposing fetch_news, summarize_text, simplify_topic, generate_digest, extract_content."""
from __future__ import annotations

from agent.tools.news_fetcher import fetch_news
from agent.tools.summarizer import summarize_text
from agent.tools.topic_simplifier import simplify_topic
from agent.tools.digest_generator import generate_digest
from agent.tools.url_extractor import extract_content

__all__ = [
    "fetch_news",
    "summarize_text",
    "simplify_topic",
    "generate_digest",
    "extract_content",
]
