"""FastAPI application for the World News & Topic Summary Agent backend.

Exposes endpoints for chat, digest generation, topic simplification, and health checks.
Wires up CORS middleware and Langfuse tracing.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env before importing settings
load_dotenv()

from config import get_settings
from models.requests import ChatRequest, DigestRequest, SimplifyRequest
from models.responses import ChatResponse, DigestResponse, SimplifyResponse, HealthResponse
from agent import run_agent, generate_session_digest, simplify_session_content
from observability.langfuse_config import is_langfuse_enabled, flush

app = FastAPI(
    title="World News & Topic Summary Agent API",
    description="Backend service hosting the conversational news agent, multi-level summarizer, and personalization workflow.",
    version="1.0.0"
)

# Load config settings
settings = get_settings()

# CORS Middleware (FR-8, Non-Functional)
# No cookies/credentials are used, so a wildcard origin is safe and keeps
# the hosted frontend (e.g. Vercel) working without extra config.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
def shutdown_event():
    """Flush pending Langfuse traces on shutdown."""
    flush()


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def health():
    """Public health check endpoint (FR-8, FR-10)."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        auth_enabled=False,
        langfuse_enabled=is_langfuse_enabled(),
        news_provider=settings.news_provider,
    )


@app.post("/api/chat", response_model=ChatResponse, tags=["Agent"])
def chat(request: ChatRequest):
    """Conversational news turn (FR-1, FR-8).

    Updates preferences, routes user intent, and returns a chat reply along
    with structured news cards.
    """
    try:
        response = run_agent(
            session_id=request.session_id,
            message=request.message,
            preferences=request.preferences
        )
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}"
        )


@app.post("/api/digest", response_model=DigestResponse, tags=["Agent"])
def digest(request: DigestRequest):
    """Personalized Daily News Digest Generation (FR-5, Route 3).

    Fetches articles across preferred categories, summarizes them, and compiles
    them into a cohesive narrative digest.
    """
    try:
        response = generate_session_digest(
            session_id=request.session_id,
            topics=request.topics,
            style=request.style
        )
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate digest: {str(e)}"
        )


@app.post("/api/simplify", response_model=SimplifyResponse, tags=["Agent"])
def simplify(request: SimplifyRequest):
    """Topic / Article Simplification (FR-4, Route 2).

    Simplifies complex concepts or extracts and summarizes a specific news article
    link at a tailored complexity level.
    """
    try:
        response = simplify_session_content(
            session_id=request.session_id,
            content=request.content,
            url=request.url,
            level=request.level
        )
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to simplify: {str(e)}"
        )
