# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a personal portfolio site for Ikeoluwa Oladele. It has two independently runnable parts:

- **Frontend**: Vue 3 SPA (`src/`) built with Vite, Tailwind CSS v4, and Vue Router
- **Backend**: Python FastAPI app (`backend/`) deployed as an Azure Function, wrapping a RAG-based AI chatbot powered by Google Gemini + Pinecone

---

## Commands

### Frontend

```bash
npm run dev        # Start Vite dev server
npm run build      # Production build
npm run lint       # ESLint with auto-fix
npm run format     # Prettier format src/
```

### Backend

The backend uses a `.venv` at `backend/.venv`.

```bash
# From the backend/ directory:
cd backend
python -m uvicorn app:app --reload           # Run FastAPI locally (port 8000)

# Run all tests
python -m pytest tests/

# Run a single test file
python -m pytest tests/test_bot.py

# Run a single test by name
python -m pytest tests/test_bot.py::BotTests::test_off_topic_question_skips_retrieval_and_llm

# Seed the Pinecone topic-gate index
python scripts/seed_questions.py
python scripts/seed_questions.py --file my_questions.json --index questions
```

Tests use `unittest.IsolatedAsyncioTestCase` (Python stdlib); pytest discovers and runs them.

### Environment Setup

Copy the two env examples before starting:

```bash
cp .env.example .env               # Frontend VITE_* variables
cp backend/.env.example backend/.env   # Backend API keys
```

---

## Architecture

### Frontend (`src/`)

- **`App.vue`** — root component; wraps everything in `Layout.vue` and handles route transitions
- **`components/Layout.vue`** — provides the global chat context via Vue `provide`/`inject`; owns `ChatBox` state and `activeProjectContext`
- **`components/ChatBox.vue`** — chat panel; maintains per-project and global conversation histories keyed by project name; sends the full `context` array to `VITE_BOT_URL`; renders responses with `markdown-it`
- **`views/ProjectView.vue`** — project browser; calls `setActiveProjectChatContext` inject so `Layout` knows which project the user is viewing; falls back to `src/data/projects.json` when the API is unavailable
- **`router/index.js`** — routes: `/`, `/introduction`, `/about`, `/projects`, `/gallery`, `/resume`

Chat project context flows: `ProjectView` → inject → `Layout` → `ChatBox` prop.

### Backend (`backend/`)

**Entry points:**
- `app.py` — FastAPI app (local dev via uvicorn)
- `function_app.py` — Azure Functions V2 wrapper; uses `AsgiMiddleware` to delegate to the FastAPI app

**Request path for `/api/chat`:**
1. `routes/chat.py` — rate-limit check (IP + UA fingerprint), then delegates to `BotService`
2. `services/Bot.py::BotService.generate_response` — builds routing query → topic gate → builds retrieval query → Pinecone retrieval → Gemini generation
3. `services/topic_gate.py::TopicGate` — queries the `questions` Pinecone index; blocks off-topic questions below `TOPIC_GATE_THRESHOLD`
4. `services/pinecone_service.py::PineconeService` — singleton; uses `query_similar_namespaces` to fan out across all namespaces in the `portfolio` index; uses `multilingual-e5-large` embedding + `pinecone-rerank-v0` reranker

**Other routes:**
- `GET /api/projects` — fetches GitHub repos with the `portfolio` topic; reads `.github/project.json` for metadata
- `POST /api/github/webhook` — HMAC-verified; on `push`/`public`/`repository` events, calls `ProjectIngestionService` to upsert/delete Pinecone namespaces. Namespace format: `github:<owner>:<repo-name>`
- `POST /admin/projects/{repo_name}/context` — admin-key-protected; upserts manual context into Pinecone
- `GET/POST /api/gallery/*` — poem/comment/like CRUD backed by Azure Table Storage (falls back to in-memory when `AZURE_TABLE_CONNECTION_STRING` is absent)

**Dependency injection** (`src/dependencies.py`): FastAPI `Depends` + `lru_cache` for singletons (`PineconeService`, `GalleryService`, `RateLimiter`).

**`PineconeService`** is a singleton (via `__new__`) initialized once at app startup via `lifespan`. It holds a `ThreadPoolExecutor` for parallel text chunking. Pinecone index uses `multilingual-e5-large` integrated embeddings (no separate embedding step needed).

**RAG data flow:**
- GitHub repos are indexed into Pinecone at `PORTFOLIO_CONTEXT_INDEX` (`portfolio` index), one namespace per repo (`github:<owner>:<repo>`)
- The `questions` index is seeded via `scripts/seed_questions.py` and is used only by the topic gate
- `BotService.build_routing_query` includes up to 4 prior turns + selected project for topic-gate context; `build_retrieval_query` only adds selected project context (not full chat history)

**Rate limiting:** defaults to 12 requests/60s per visitor; persisted in Azure Table `RateLimits` if `AZURE_TABLE_CONNECTION_STRING` is set, otherwise in-process memory.

### Key Config (`backend/src/config/settings.py`)

| Variable | Default | Purpose |
|---|---|---|
| `PORTFOLIO_CONTEXT_INDEX` | `portfolio` | Pinecone index for RAG content |
| `TOPIC_GATE_INDEX` | `questions` | Pinecone index for topic-gate similarity |
| `TOPIC_GATE_THRESHOLD` | `0.00005` | Minimum reranker score to allow a question through |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Generation model |
| `GITHUB_PROJECT_TOPIC` | `portfolio` | GitHub topic tag that marks repos for ingestion |
