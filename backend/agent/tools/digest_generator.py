"""Digest generator tool (FR-5, Route 3).

Fetches news across multiple topics, summarizes the articles, and compiles them
into a single, cohesive daily digest narrative.
Uses Gemini when keys are present, and generates a formatted newsletter in offline mode.
"""
from __future__ import annotations

from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import get_settings
from agent.tools.news_fetcher import fetch_news
from agent.tools.summarizer import summarize_text


def generate_digest(
    topics: List[str],
    style: str = "simple",
    complexity: str = "beginner",
    reading_frequency: str = "medium"
) -> tuple[str, int]:
    """Compile a personalized news digest across multiple topics.

    Returns a tuple of (digest_text, articles_included_count).
    """
    settings = get_settings()
    
    # 1. Fetch news articles for each topic
    # The count per topic depends on reading frequency
    articles_per_topic = 2
    if reading_frequency == "low":
        articles_per_topic = 1
    elif reading_frequency == "high":
        articles_per_topic = 3

    all_articles = []
    for topic in topics:
        topic_articles = fetch_news(topic, count=articles_per_topic)
        all_articles.extend(topic_articles)

    if not all_articles:
        return "No articles found for the selected topics to generate a digest.", 0

    # 2. Summarize each article individually
    summarized_chunks = []
    for idx, article in enumerate(all_articles):
        # We can extract text or pass the title + description
        content_to_summarize = f"Title: {article.title}\nDescription: {article.description}\nSource: {article.source}\nDate: {article.published_date}"
        summary = summarize_text(content_to_summarize, level=style)
        summarized_chunks.append({
            "topic": article.category,
            "title": article.title,
            "source": article.source,
            "summary": summary,
            "url": article.url
        })

    # 3. Compile the summaries into a unified narrative
    has_gemini = settings.gemini_api_key and settings.gemini_api_key != "your-gemini-api-key" and "your_api_key" not in settings.gemini_api_key

    if has_gemini:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            llm = ChatGoogleGenerativeAI(
                google_api_key=settings.gemini_api_key,
                model=settings.gemini_model_name,
                temperature=0.3,
            )

            # Format the raw summaries for the LLM
            formatted_inputs = []
            for item in summarized_chunks:
                formatted_inputs.append(
                    f"Category: {item['topic'].upper()}\n"
                    f"Headline: {item['title']} (Source: {item['source']})\n"
                    f"Summary: {item['summary']}\n"
                    f"URL: {item['url']}\n"
                    "---"
                )
            raw_data = "\n".join(formatted_inputs)

            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are a professional news editor. Compile the provided individual summaries "
                    "into a single, cohesive, human-friendly daily newsletter. Do not just list them; "
                    "synthesize them with smooth transitions, group by category, and tailor the style "
                    f"to a '{style}' format with explanation complexity at '{complexity}' level. "
                    "Make sure to reference the headlines, sources, and include the original URLs in parenthesis next to the mention so the reader can read more."
                )),
                ("user", "Here are the summaries to compile:\n\n{summaries}")
            ])
            
            chain = prompt | llm | StrOutputParser()
            compiled_digest = chain.invoke({"summaries": raw_data})
            return compiled_digest, len(all_articles)
        except Exception as e:
            print(f"Gemini digest compiler failed: {e}. Using mock digest compilation.")

    # 4. Fallback / Mock digest compilation (highly structured newsletter)
    return _compile_mock_digest(summarized_chunks, style, complexity), len(all_articles)


def _compile_mock_digest(summarized_chunks: List[dict], style: str, complexity: str) -> str:
    """Format and synthesize the summaries deterministically for mock mode."""
    lines = []
    lines.append("📰 **YOUR PERSONALIZED DAILY DIGEST** 📰")
    lines.append("Here is your curated newsletter summarizing today's key updates.\n")

    # Group by category
    by_category = {}
    for item in summarized_chunks:
        cat = item["topic"].upper()
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)

    for cat, items in by_category.items():
        lines.append(f"### ─── {cat} ───")
        for item in items:
            lines.append(f"**{item['title']}** (Source: *{item['source']}*)")
            lines.append(f"{item['summary']}")
            if item['url']:
                lines.append(f"[Read full article]({item['url']})")
            lines.append("")

    lines.append("---")
    lines.append(f"*Preferences Applied: Summary Style = {style.capitalize()} | Complexity = {complexity.capitalize()}*")
    lines.append("You are all caught up! Have a wonderful day. ☀️")
    
    return "\n".join(lines)
