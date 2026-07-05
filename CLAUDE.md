# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a personal portfolio site for Ikeoluwa Oladele. It has two independently runnable parts:

- **Frontend**: Vue 3 SPA (`src/`) built with Vite, Tailwind CSS v4, and Vue Router
- **Backend**: Python FastAPI app (`backend/`) deployed as an Azure App Service for Containers, wrapping a RAG-based AI chatbot powered by Google Gemini + Pinecone

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
python -m pytest tests/test_bot.py::BotTests::test_off_topic_question_skips_rerank_and_llm
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
- **`components/ChatBox.vue`** — chat panel; maintains per-project and global conversation histories keyed by project name; sends the full `context` array to `VITE_BOT_URL`; reads the streamed response body incrementally; renders with `markdown-it`
- **`components/Layout.vue`** — closes chat on outside click (transparent backdrop) and on route navigation
- **`views/ProjectView.vue`** — project browser; calls `setActiveProjectChatContext` inject so `Layout` knows which project the user is viewing; falls back to `src/data/projects.json` when the API is unavailable
- **`router/index.js`** — routes: `/`, `/introduction`, `/about`, `/projects`, `/gallery`, `/resume`

Chat project context flows: `ProjectView` → inject → `Layout` → `ChatBox` prop.

### Backend (`backend/`)

**Entry points:**
- `app.py` — FastAPI app (local dev via uvicorn)

**Request path for `/api/chat`:**
1. `routes/chat.py` — rate-limit check (IP + UA fingerprint), returns a `StreamingResponse` from `BotService.stream_response`
2. `services/Bot.py::BotService.stream_response` — runs `ChatResolver` and `PineconeService.fetch_candidates` in parallel via `asyncio.gather`; gates reranking on resolver relevance; reranks using the resolver's standalone question; streams Gemini generation token-by-token
3. `services/chat_resolver.py::ChatResolver` — single Gemini call that classifies relevance and rewrites follow-ups into standalone questions
4. `services/pinecone_service.py::PineconeService` — singleton; `fetch_candidates` queries project namespaces in parallel (scoped to `github:<owner>:<repo>` + `:manual` when project context is present, otherwise all namespaces); `rerank_candidates` fires one `pinecone-rerank-v0` call on the merged pool (skipped when pool ≤ `PINECONE_QUERY_TOP_N`); uses `multilingual-e5-large` integrated embeddings

**Other routes:**
- `GET /api/projects` — fetches GitHub repos with the `portfolio` topic; reads `.github/project.json` for metadata
- `POST /api/github/webhook` — HMAC-verified; on `push`/`public`/`repository` events, calls `ProjectIngestionService` to upsert/delete Pinecone namespaces. Namespace format: `github:<owner>:<repo-name>`
- `POST /admin/projects/{repo_name}/context` — admin-key-protected; upserts manual context into Pinecone
- `GET/POST /api/gallery/*` — poem/comment/like CRUD backed by Azure Table Storage (falls back to in-memory when `AZURE_TABLE_CONNECTION_STRING` is absent)

**Dependency injection** (`src/dependencies.py`): FastAPI `Depends` + `lru_cache` for singletons (`PineconeService`, `GalleryService`, `RateLimiter`).

**`PineconeService`** is a singleton (via `__new__`) initialized once at app startup via `lifespan`. It holds a `ThreadPoolExecutor` for parallel text chunking. Pinecone index uses `multilingual-e5-large` integrated embeddings (no separate embedding step needed).

**RAG data flow:**
- GitHub repos are indexed into Pinecone at `PORTFOLIO_CONTEXT_INDEX` (`portfolio` index), one namespace per repo (`github:<owner>:<repo>`); manual context lives in `github:<owner>:<repo>:manual`
- When a user is on a project page, the frontend includes a hidden context message with the GitHub source URL; `Bot._extract_project_namespaces` parses it to scope retrieval to those two namespaces only
- `build_retrieval_query` includes the selected project context but not full chat history; the resolver's `standalone_question` is used as the rerank query for better precision on follow-ups

**Rate limiting:** defaults to 12 requests/60s per visitor; persisted in Azure Table `RateLimits` if `AZURE_TABLE_CONNECTION_STRING` is set, otherwise in-process memory.

### Key Config (`backend/src/config/settings.py`)

| Variable | Default | Purpose |
|---|---|---|
| `PORTFOLIO_CONTEXT_INDEX` | `portfolio` | Pinecone index for RAG content |
| `PINECONE_QUERY_TOP_K` | `3` | Candidates fetched per namespace (vector-only) |
| `PINECONE_QUERY_TOP_N` | `3` | Final results after reranking |
| `PINECONE_NAMESPACE_CACHE_TTL` | `300` | Seconds to cache namespace list |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Model used for both resolver and generation |
| `GITHUB_PROJECT_TOPIC` | `portfolio` | GitHub topic tag that marks repos for ingestion |
| `GITHUB_REPOS_PER_PAGE` | `100` | Repos fetched per GitHub API page |
| `GITHUB_REPOS_TYPE` | `owner` | Repo ownership filter for GitHub API |
| `GITHUB_REPOS_SORT` | `updated` | Sort order for GitHub repo listing |
| `BUILD_COMMIT` | `dev` | Git SHA baked in at Docker build time; returned by `/health` |
