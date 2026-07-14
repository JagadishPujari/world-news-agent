# World News & Topic Summary Agent

An intelligent conversational AI agent that fetches global news, summarizes articles at multiple levels, simplifies complex topics, and delivers personalized daily digests—with full observability. No login required.

---

## Overview

This project implements a **full-stack AI-powered news assistant** (Backend: FastAPI + LangChain + Gemini, Frontend: React + Vite) that solves six core user challenges:

1. **Information Overload** → Agent filters and prioritizes news
2. **Complex Articles** → 3-level summaries (simple, detailed, bullets)
3. **Lack of Personalization** → Session-scoped preferences
4. **Fragmented Sources** → Unified chat interface
5. **Time Constraints** → Concise summaries on demand
6. **No Session Awareness** → Remembers favorite topics during session

---

## Architecture

```
┌─────────────────────────────────────┐
│    React Frontend (Vite)            │
│  ├─ Chat Interface                 │
│  ├─ Topic Selector                 │
│  ├─ News Cards                     │
│  ├─ Digest/Simplify Buttons        │
│  └─ Preferences Panel              │
└─────────────────┬───────────────────┘
                  │ REST (JSON)
                  ▼
┌─────────────────────────────────────┐
│   FastAPI Backend (Python)          │
│  ├─ 4 API Routes                   │
│  ├─ LangChain Agent + Tools        │
│  ├─ Session Memory (per session)   │
│  └─ Langfuse Tracing ✓             │
└─────────────────┬───────────────────┘
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
   ┌─────────────┐   ┌──────────────┐
   │ NewsData.io │   │ Langfuse     │
   │CurrentsAPI  │   │ Observability│
   └─────────────┘   └──────────────┘
```

### Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend** | FastAPI, Uvicorn | 0.115+ |
| **LLM** | Google Gemini | 1.5-pro |
| **Agent Framework** | LangChain | 0.3+ |
| **Observability** | Langfuse | 2.54+ |
| **News Data** | NewsData.io / CurrentsAPI | REST APIs |
| **Frontend** | React + Vite + TypeScript | 18+, 5+ |

---

## Installation & Setup

### 1. Prerequisites

- Python 3.9+ with pip
- Node.js 16+ with npm
- Gemini API key (free: https://aistudio.google.com) — optional; mock data is used if absent
- NewsData.io OR CurrentsAPI key — optional; mock data is used if absent
- Langfuse account (optional)

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your keys (all optional — mock data is used as fallback):
#   GEMINI_API_KEY
#   LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_HOST
#   NEWSDATA_API_KEY or CURRENTS_API_KEY
```

### 3. Run Backend

```bash
# From backend/ directory
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The backend will start on `http://localhost:8000`.
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Health Check:** `GET http://localhost:8000/api/health`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# (Optional) point the frontend at a hosted backend:
# echo "VITE_API_BASE_URL=https://your-backend-host" > .env

# Run dev server
npm run dev
```

Frontend will start on `http://localhost:5173`.

**Frontend Features Implemented:**
- ✅ Chat interface with multi-turn conversation
- ✅ Topic selector (politics, sports, technology, finance, climate)
- ✅ News cards with title, source, date, URL, simplify button
- ✅ Preferences panel (summary style, complexity, frequency)
- ✅ Digest generator panel

---

## API Reference

All endpoints are open — no authentication headers required.

### 1. Health Check
```http
GET /api/health
```

**Response (200):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "auth_enabled": false,
  "langfuse_enabled": true,
  "news_provider": "newsdata"
}
```

### 2. Chat (FR-1, Route 1)
```http
POST /api/chat
Content-Type: application/json

{
  "session_id": "user-123",
  "message": "Show me tech news",
  "preferences": {
    "topics": ["technology", "finance"],
    "summary_style": "simple",
    "complexity": "beginner",
    "reading_frequency": "medium"
  }
}
```

**Response (200):**
```json
{
  "session_id": "user-123",
  "reply": "Here are the latest tech headlines...",
  "news_items": [
    {
      "title": "AI Breakthrough",
      "description": "...",
      "source": "TechCrunch",
      "url": "https://...",
      "published_date": "2026-06-18",
      "category": "technology"
    }
  ],
  "workflow_used": "topic_news",
  "trace_id": "trace-abc123"
}
```

### 3. Digest (FR-5, Route 3)
```http
POST /api/digest
Content-Type: application/json

{
  "session_id": "user-123",
  "topics": ["technology", "finance"],
  "style": "simple"
}
```

**Response (200):**
```json
{
  "session_id": "user-123",
  "digest": "📰 YOUR PERSONALIZED DAILY DIGEST...",
  "articles_included": 6,
  "topics": ["technology", "finance"],
  "trace_id": "trace-xyz789"
}
```

### 4. Simplify (FR-4, Route 2)
```http
POST /api/simplify
Content-Type: application/json

{
  "session_id": "user-123",
  "content": "geopolitical conflicts",
  "url": null,
  "level": "beginner"
}
```

**Response (200):**
```json
{
  "session_id": "user-123",
  "simplified": "Geopolitical conflict is like a playground argument...",
  "source_url": null,
  "trace_id": "trace-def456"
}
```

---

## Multi-Step Workflows

### Route 1: Topic News
```
User: "Show me climate news"
  └─► Agent detects: FETCH_NEWS
        └─► fetch_news_tool(topic="climate", count=10)
              └─► LLM structures and presents headlines
                    └─► Response: News cards with titles, sources, URLs
```

### Route 2: URL Ingestion & Simplification
```
User: "Summarize https://example.com/article"
  └─► Agent detects: URL in message
        └─► extract_url_tool(url)
              └─► summarize_tool(extracted_text, level="simple")
                    └─► Response: Clean summary at user's preferred level
```

### Route 3: Daily Digest
```
User: "Generate my daily digest" or clicks "Digest" button
  └─► Agent detects: GENERATE_DIGEST
        └─► Read session memory: [favorite topics, style]
              └─► fetch_news_tool(each topic, count=2-5)
                    └─► summarize_tool(each article)
                          └─► generate_digest_tool(all summaries)
                                └─► Response: Compiled newsletter
```

---

## Features Implemented

### Functional Requirements (FR)

| # | Requirement | Status |
|---|---|---|
| FR-1 | Conversational News Assistant | ✅ |
| FR-2 | External News API Integration | ✅ |
| FR-3 | Real-Time News Discovery (5–10 headlines) | ✅ |
| FR-4 | Multi-Level Summaries & Topic Simplification | ✅ |
| FR-5 | Personalized Daily Digest | ✅ |
| FR-6 | Multi-Step Workflow Routing (3 routes) | ✅ |
| FR-7 | Short-Term Session Memory | ✅ |
| FR-8 | FastAPI Backend | ✅ |
| FR-9 | Langfuse Observability | ✅ |
| FR-10 | Frontend (React + Vite) | ✅ |

### Session Memory (FR-7)
Persisted **per session** during a single conversation:
- Favorite categories
- Preferred complexity level
- Previously viewed topics
- Preferred summary length/style

**Memory resets** when:
- Session is explicitly cleared
- Backend restarts
- The browser page is refreshed (a new session id is generated)

---

## Observability with Langfuse

All LLM calls, tool invocations, and workflows are traced to Langfuse for debugging and monitoring.

### Traced Events
- ✅ LLM outputs (prompts, completions, tokens)
- ✅ Summaries generated (level, complexity)
- ✅ API calls to news providers (topic, count, latency)
- ✅ Workflow paths taken (route detection)
- ✅ Latency per request
- ✅ Errors and retries

### View Traces
1. Log into https://cloud.langfuse.com
2. Select your project
3. Browse traces grouped by `session_id`
4. Inspect tool calls, LLM prompts, and latency

**Example Trace Screenshot:**
```
[Langfuse Trace View — showing:
 - session_id: user-123
 - workflow: topic_news
 - fetch_news_tool call: topic=technology, count=10
 - LangChain agent step: invoke tool
 - summarize_tool call: 3 articles summarized at level=simple
 - Total latency: 2.3s
]
```

---

## Deployment (Vercel)

### Frontend
1. Import the repo in https://vercel.com/new and set **Root Directory** to `frontend/`.
2. Framework preset: **Vite** (auto-detected via `frontend/vercel.json`).
3. Add environment variable `VITE_API_BASE_URL` pointing at your hosted backend URL.
4. Deploy — done.

### Backend
`backend/vercel.json` is included so the FastAPI app can be deployed as a Vercel
Python serverless function (set **Root Directory** to `backend/` in a second
Vercel project, and add the backend env vars from `.env.example`).

> Note: the LangChain dependency set is large and may exceed Vercel's serverless
> bundle limit. If the backend deploy fails on size, host it on Render/Railway
> (a plain `uvicorn app:app --host 0.0.0.0 --port $PORT` service) and point
> `VITE_API_BASE_URL` at that URL instead. Session memory is in-process, so on
> serverless platforms sessions reset between invocations.

---

## Environment Variables

| Variable | Purpose | Example |
|---|---|---|
| `GEMINI_API_KEY` | Gemini LLM auth | `AIzaSy...` |
| `GEMINI_MODEL_NAME` | Model to use | `gemini-3.5-flash` |
| `LANGFUSE_SECRET_KEY` | Langfuse auth | `sk-lf-...` |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key | `pk-lf-...` |
| `LANGFUSE_HOST` | Langfuse endpoint | `https://cloud.langfuse.com` |
| `NEWSDATA_API_KEY` | NewsData.io key | `abc123...` |
| `CURRENTS_API_KEY` | CurrentsAPI key | `xyz789...` |
| `NEWS_PROVIDER` | Primary provider | `newsdata` or `currents` |
| `FRONTEND_ORIGIN` | CORS allowed origin | `http://localhost:5173` |
| `VITE_API_BASE_URL` | (Frontend) backend base URL | `https://your-backend.example.com` |

---

## File Structure

```
world-news-agent/
├── backend/
│   ├── app.py                       # FastAPI app & routes
│   ├── config.py                    # Settings from env
│   ├── requirements.txt
│   ├── vercel.json                  # Vercel Python deployment config
│   ├── .env.example
│   ├── observability/
│   │   └── langfuse_config.py       # Langfuse client & callbacks
│   ├── models/
│   │   ├── requests.py              # Request schemas
│   │   └── responses.py             # Response schemas
│   └── agent/
│       ├── news_agent.py            # LangChain agent + rule-based fallback
│       ├── session_store.py         # In-memory session store
│       ├── llm.py                   # Gemini LLM factory
│       └── tools/
│           ├── news_fetcher.py      # Fetch news from APIs
│           ├── summarizer.py        # 3-level summaries
│           ├── topic_simplifier.py  # Simplify complex topics
│           ├── digest_generator.py  # Compile daily digest
│           └── url_extractor.py     # Extract text from URLs
├── frontend/
│   ├── vercel.json                  # Vercel SPA deployment config
│   └── src/                         # React + Vite app
└── README.md
```

---

## Testing & Validation

### 1. Backend Health
```bash
curl http://localhost:8000/api/health
```

Expected: `{"status": "ok", "version": "1.0.0", ...}`

### 2. Chat Endpoint
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "message": "Show me technology news"
  }'
```

### 3. Digest Endpoint
```bash
curl -X POST http://localhost:8000/api/digest \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "topics": ["technology", "finance"]
  }'
```

---

## Troubleshooting

### Missing API Keys
If `GEMINI_API_KEY` or news API keys are missing or are placeholder values, the system falls back to high-fidelity mock data. This is intentional for offline development but should not be used in production.

### Langfuse Traces Not Appearing
1. Verify `LANGFUSE_SECRET_KEY` and `LANGFUSE_PUBLIC_KEY` are correct
2. Check `LANGFUSE_HOST` is reachable
3. Call `/api/health` to see `langfuse_enabled` status

---

## Performance & Scalability

### Session Memory
- In-memory dictionary (process-scoped)
- Scales to ~1,000 concurrent sessions per process
- For larger deployments, migrate to Redis or database

### News API Rate Limits
- NewsData.io: 200 req/day (free) → 50k/day (paid)
- CurrentsAPI: 600 req/day (free)
- Implement caching layer for production

### LLM Latency
- Typical `fetch_news` → `summarize`: 2–4 seconds
- Digest compilation (multi-topic): 5–10 seconds

---

## Deliverables Checklist

- ✅ FastAPI Backend with LangChain Agent
- ✅ External News API Integration (NewsData.io + CurrentsAPI with fallback)
- ✅ Langfuse Observability (all 6 trace types)
- ✅ Frontend (React + Vite)
- ✅ README (setup, architecture, API docs, workflows)

---

## Getting Help

- **API Documentation (Live):** http://localhost:8000/docs
- **Langfuse Traces:** https://cloud.langfuse.com
- **NewsData.io Docs:** https://newsdata.io/docs
- **LangChain Docs:** https://python.langchain.com

---

## License

This project is part of the AI Hackathon. Use freely for educational and research purposes.
