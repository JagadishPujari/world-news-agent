"""Conversational agent pipeline (FR-1, FR-6, FR-8).

Configures LangChain tools, initializes the Gemini LLM with Langfuse tracing,
manages session history, and handles graceful mock fallbacks.
"""
from __future__ import annotations

import re
from contextvars import ContextVar
from typing import List, Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage

from config import get_settings
from agent.session_store import session_store, UserPreferences
from agent.tools.news_fetcher import fetch_news
from agent.tools.summarizer import summarize_text
from agent.tools.topic_simplifier import simplify_topic
from agent.tools.digest_generator import generate_digest
from agent.tools.url_extractor import extract_content
from models.responses import ChatResponse, DigestResponse, SimplifyResponse, NewsItem, WorkflowName
from observability.langfuse_config import get_langfuse_handler


# Request-scoped ContextVars to capture structural data populated by tools
news_items_var: ContextVar[List[NewsItem]] = ContextVar("news_items", default=[])
workflow_used_var: ContextVar[WorkflowName] = ContextVar("workflow_used", default="conversation")


# ── LangChain Tool Definitions ────────────────────────────────

@tool
def fetch_news_tool(topic: str, count: int = 5) -> str:
    """Retrieve news articles for a specific topic or search query. Returns the raw headlines and details."""
    items = fetch_news(topic, count=count)
    # Store in context variable for API response
    news_items_var.set(news_items_var.get() + items)
    workflow_used_var.set("topic_news")
    
    formatted = []
    for item in items:
        formatted.append(
            f"Title: {item.title}\n"
            f"Description: {item.description}\n"
            f"Source: {item.source}\n"
            f"Date: {item.published_date}\n"
            f"URL: {item.url}\n"
            "---"
        )
    return "\n".join(formatted)


@tool
def summarize_tool(content: str, level: str = "simple") -> str:
    """Generate a summary of article content at a specific level ('simple', 'detailed', 'bullets')."""
    return summarize_text(content, level)


@tool
def simplify_topic_tool(topic: str, complexity: str = "beginner") -> str:
    """Explain a complex concept in simple terms matching a complexity level ('beginner', 'intermediate', 'expert')."""
    return simplify_topic(topic, complexity)


@tool
def generate_digest_tool(topics: List[str], style: str = "simple", complexity: str = "beginner", reading_frequency: str = "medium") -> str:
    """Generate a cohesive daily digest newsletter compiled across multiple topics."""
    workflow_used_var.set("daily_digest")
    digest, _ = generate_digest(topics, style, complexity, reading_frequency)
    return digest


@tool
def extract_url_tool(url: str) -> str:
    """Extract plain text body content from a web page URL."""
    workflow_used_var.set("url_ingestion")
    return extract_content(url)


# List of tools for LangChain agent
_TOOLS = [
    fetch_news_tool,
    summarize_tool,
    simplify_topic_tool,
    generate_digest_tool,
    extract_url_tool,
]


# ── Agent Execution Entrypoints ───────────────────────────────

def run_agent(
    session_id: str,
    message: str,
    preferences: Optional[UserPreferences] = None
) -> ChatResponse:
    """Run a single chat turn. Resolves LLM vs. Rule-based flow, handles memory and tracing."""
    settings = get_settings()
    
    # 1. Fetch or create session state
    state = session_store.get_or_create(session_id)
    if preferences:
        state.preferences = preferences

    # Reset ContextVars for this request
    news_items_var.set([])
    workflow_used_var.set("conversation")

    # Check for Gemini keys to determine execution path
    has_gemini = settings.gemini_api_key and settings.gemini_api_key != "your-gemini-api-key" and "your_api_key" not in settings.gemini_api_key

    trace_id = None
    reply = ""

    if has_gemini:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            # Setup LangChain Gemini LLM
            llm = ChatGoogleGenerativeAI(
                google_api_key=settings.gemini_api_key,
                model=settings.gemini_model_name,
                temperature=0.3,
            )

            # Define System Prompt injecting user preferences
            system_prompt = (
                "You are an intelligent World News & Topic Summary Agent, a conversational companion.\n"
                "You fetch global news, summarize articles, simplify complex topics, and deliver daily digests.\n\n"
                "User Preferences to apply in this session:\n"
                f"- Favorite Topics: {', '.join(state.preferences.topics) if state.preferences.topics else 'None specified'}\n"
                f"- Summary Style: {state.preferences.summary_style}\n"
                f"- Explanation Complexity: {state.preferences.complexity}\n"
                f"- Reading Frequency: {state.preferences.reading_frequency}\n\n"
                "Rules:\n"
                "1. If user asks for news, use fetch_news_tool to get articles, then write a summary using the preferred style.\n"
                "2. If user shares a URL, call extract_url_tool and summarize the extracted text.\n"
                "3. If they ask for a newsletter/digest, call generate_digest_tool.\n"
                "4. When simplifying complex subjects, call simplify_topic_tool with the requested complexity.\n"
                "5. Maintain conversation history."
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            # Build Agent
            agent = create_tool_calling_agent(llm, _TOOLS, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=_TOOLS, verbose=True)

            # Map chat history to LangChain Message structures
            lc_history = []
            for msg in state.chat_history[-10:]:  # Keep window size 10
                if msg["role"] == "user":
                    lc_history.append(HumanMessage(content=msg["content"]))
                else:
                    lc_history.append(AIMessage(content=msg["content"]))

            # Setup Langfuse Tracing Handler
            handler = get_langfuse_handler(
                session_id=session_id,
                workflow=workflow_used_var.get(),
                tags=["chat"],
            )
            callbacks = [handler] if handler else []

            # Execute
            result = agent_executor.invoke(
                {"input": message, "chat_history": lc_history},
                config={"callbacks": callbacks}
            )
            reply = result["output"]
            # Gemini can return the output as a list of content parts.
            if isinstance(reply, list):
                reply = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in reply
                )

            if handler and hasattr(handler, "get_trace_id"):
                trace_id = handler.get_trace_id()

            # A rate-limited/failed LLM turn can surface as an empty output
            # instead of an exception — treat it as a failure.
            if not reply or not reply.strip():
                print("LangChain agent returned an empty reply. Falling back to Rule-based mock agent.")
                has_gemini = False

        except Exception as e:
            print(f"Failed to run LangChain agent: {e}. Falling back to Rule-based mock agent.")
            has_gemini = False

    if not has_gemini:
        # Run Rule-based mock agent
        reply = _run_mock_agent_logic(state, message)

    # 4. Save message pair in history
    session_store.add_message(session_id, "user", message)
    session_store.add_message(session_id, "assistant", reply)

    # 5. Extract results
    return ChatResponse(
        session_id=session_id,
        reply=reply,
        news_items=news_items_var.get(),
        workflow_used=workflow_used_var.get(),
        trace_id=trace_id
    )


def generate_session_digest(
    session_id: str,
    topics: Optional[List[str]] = None,
    style: Optional[str] = None
) -> DigestResponse:
    """Route 3 Direct Endpoint: Compile daily digest for a session."""
    state = session_store.get_or_create(session_id)
    
    # Use parameters or fall back to session preferences
    selected_topics = topics if topics is not None else state.preferences.topics
    if not selected_topics:
        # Default topics if none are set
        selected_topics = ["politics", "technology", "climate"]

    selected_style = style if style is not None else state.preferences.summary_style
    
    # Track workflow
    workflow_used_var.set("daily_digest")

    # Generate
    digest, count = generate_digest(
        topics=selected_topics,
        style=selected_style,
        complexity=state.preferences.complexity,
        reading_frequency=state.preferences.reading_frequency
    )

    # Save to chat history
    session_store.add_message(session_id, "user", f"Generate daily digest for: {', '.join(selected_topics)}")
    session_store.add_message(session_id, "assistant", digest)

    return DigestResponse(
        session_id=session_id,
        digest=digest,
        articles_included=count,
        topics=selected_topics
    )


def simplify_session_content(
    session_id: str,
    content: str,
    url: Optional[str] = None,
    level: Optional[str] = None
) -> SimplifyResponse:
    """Route 2 / FR-4 Direct Endpoint: Simplify a topic, text content, or URL."""
    state = session_store.get_or_create(session_id)
    selected_level = level if level is not None else state.preferences.complexity

    # Track workflow
    if url:
        workflow_used_var.set("url_ingestion")
        raw_text = extract_content(url)
        # Summarize the extracted URL content at the requested style level
        simplified = summarize_text(raw_text, level="simple" if selected_level == "beginner" else "detailed")
    else:
        # Just simplify the text/topic
        workflow_used_var.set("conversation")
        simplified = simplify_topic(content, complexity=selected_level)

    # Save to chat history
    prompt_msg = f"Simplify article from: {url}" if url else f"Simplify topic: {content}"
    session_store.add_message(session_id, "user", prompt_msg)
    session_store.add_message(session_id, "assistant", simplified)

    return SimplifyResponse(
        session_id=session_id,
        simplified=simplified,
        source_url=url
    )


# ── Rule-Based Fallback Agent Logic ────────────────────────────

def _run_mock_agent_logic(state: any, message: str) -> str:
    """Deterministic, high-fidelity conversational mock agent."""
    msg = message.lower().strip()

    # Detect URLs
    url_match = re.search(r'https?://[^\s]+', message)
    
    # 1. Route 2: URL Ingestion
    if url_match:
        url = url_match.group(0)
        workflow_used_var.set("url_ingestion")
        raw_text = extract_content(url)
        summary = summarize_text(raw_text, level=state.preferences.summary_style)
        return (
            f"I have successfully extracted the content from {url}.\n\n"
            f"Here is a **{state.preferences.summary_style}** summary based on your preferences:\n\n{summary}"
        )

    # 2. Route 3: Daily Digest Request
    if "digest" in msg or "newsletter" in msg or "summary digest" in msg:
        workflow_used_var.set("daily_digest")
        topics = state.preferences.topics if state.preferences.topics else ["politics", "technology", "climate"]
        digest, _ = generate_digest(
            topics=topics,
            style=state.preferences.summary_style,
            complexity=state.preferences.complexity,
            reading_frequency=state.preferences.reading_frequency
        )
        return digest

    # 3. Route 1: Topic News
    # Look for known interest categories
    matched_topic = None
    for topic in ["politics", "sports", "technology", "finance", "climate"]:
        if topic in msg:
            matched_topic = topic
            break

    if "news" in msg or "headlines" in msg or matched_topic:
        topic_to_fetch = matched_topic or "technology"
        workflow_used_var.set("topic_news")
        
        # Save preference in viewed topics
        session_store.record_viewed_topic(state.session_id, topic_to_fetch)
        
        items = fetch_news(topic_to_fetch, count=3)
        # Save to contextvar
        news_items_var.set(items)
        
        reply_lines = [
            f"Here are the latest news updates for **{topic_to_fetch.capitalize()}**:\n",
        ]
        for idx, item in enumerate(items, 1):
            reply_lines.append(f"{idx}. **{item.title}** (Source: *{item.source}* - {item.published_date})")
            # Generate a quick simple summary for each
            summary = summarize_text(item.description or item.title, level=state.preferences.summary_style)
            reply_lines.append(f"   *Summary: {summary}*")
            if item.url:
                reply_lines.append(f"   [Read More]({item.url})")
            reply_lines.append("")
            
        reply_lines.append(f"Would you like me to simplify any of these topics, or generate a full daily digest?")
        return "\n".join(reply_lines)

    # 4. Simplify topic requests
    if "simplify" in msg or "explain" in msg:
        concept = message
        # Strip out command words
        for w in ["simplify", "explain", "please", "me", "what is", "about"]:
            concept = re.sub(rf'\b{w}\b', '', concept, flags=re.IGNORECASE)
        concept = concept.strip()
        if not concept:
            concept = "geopolitical conflicts"
            
        workflow_used_var.set("conversation")
        explanation = simplify_topic(concept, complexity=state.preferences.complexity)
        return (
            f"Here is a beginner-friendly explanation of **{concept}**:\n\n"
            f"{explanation}\n\n"
            f"*Complexity: {state.preferences.complexity.capitalize()}*"
        )

    # 5. Generic Conversation
    workflow_used_var.set("conversation")
    return (
        f"Hello! I am your AI News Companion. I remember your interests during this session.\n\n"
        f"Currently, your preferences are set to:\n"
        f"- **Favorite Topics**: {', '.join(state.preferences.topics) if state.preferences.topics else 'None (tell me what you like!)'}\n"
        f"- **Summary Style**: {state.preferences.summary_style.capitalize()}\n"
        f"- **Complexity**: {state.preferences.complexity.capitalize()}\n\n"
        f"You can ask me to:\n"
        f"- 'Show me tech news' or any of our categories: Politics, Sports, Technology, Finance, Climate\n"
        f"- Share an article link for me to summarize\n"
        f"- 'Explain quantum computing' or another complex topic\n"
        f"- 'Generate my daily digest' based on your selected interests"
    )
