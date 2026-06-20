# Personal Portfolio — Ikeoluwa Oladele

A personal portfolio site with a context-aware AI chatbot built into every page. The frontend is a Vue 3 SPA; the backend is a Python FastAPI service deployed on Azure Functions that handles the chat, project data, resume parsing, and a small gallery.

Live: <!-- add your URL here -->  
Source: [github.com/TheBluCoder/portfolio](https://github.com/TheBluCoder/portfolio)

---

## How the chatbot works

The chat panel (bottom-right on every page) is backed by a **RAG (Retrieval-Augmented Generation)** pipeline:

1. **Topic gate** — before doing anything expensive, the query is scored against a Pinecone index seeded with representative questions. Scores below a threshold short-circuit the pipeline and return a polite "I can only answer questions about Ike's work" reply. This keeps the bot on-topic without needing a separate classifier model.

2. **Retrieval** — if the query passes the gate, it's used to search a second Pinecone index that holds chunked text from every portfolio project's README and metadata. The search fans out across all project namespaces simultaneously and re-ranks the combined results with `pinecone-rerank-v0`.

3. **Generation** — the top results are injected as context into a prompt sent to Google Gemini (`gemini-flash-lite`). The model generates a grounded, conversational response.

The chat is project-aware: when you're on a project page, the bot knows which project you're looking at and weights context retrieval accordingly.

---

## Project ingestion (automated)

Every public GitHub repo tagged with the `portfolio` topic is automatically indexed:

- A GitHub webhook fires on push, visibility, and repository events
- The backend verifies the HMAC signature, fetches the repo's README and `.github/project.json`, chunks the content, and upserts it into Pinecone under the namespace `github:<owner>:<repo>`
- Deleting or privatising a repo removes its namespace

Manual context (supplementary info not in the README) can be added via the admin API without touching the repo itself.

---

## Architecture

### Frontend (`src/`)

Vue 3 · Vite · Tailwind CSS v4 · Vue Router

| Component | Responsibility |
|---|---|
| `Layout.vue` | Shell; provides chat context via Vue `provide`/`inject`; owns `ChatBox` state |
| `ChatBox.vue` | Chat UI; keeps per-project conversation history; renders markdown responses |
| `ProjectView.vue` | Fetches projects from API; sets active project context so chat knows what the user is viewing |

Routes: `/` · `/introduction` · `/about` · `/projects` · `/gallery` · `/resume`

### Backend (`backend/`)

Python 3.11 · FastAPI · Azure Functions V2

The FastAPI app runs locally with Uvicorn and is deployed as an Azure Function using `AsgiMiddleware` — the same codebase serves both environments.

**Key routes:**

| Route | Purpose |
|---|---|
| `POST /api/chat` | RAG pipeline — rate-limited, topic-gated, retrieval + Gemini generation |
| `GET /api/projects` | Lists portfolio repos from GitHub with `.github/project.json` metadata merged in |
| `GET /api/resume` | Parses a PDF resume with Gemini; result cached for 24 h |
| `GET/POST /api/gallery/*` | Poem, comment, and like CRUD |
| `GET/PUT/POST/DELETE /api/reading/*` | Reading list CRUD |
| `POST /api/github/webhook` | HMAC-verified; triggers Pinecone ingestion on repo events |
| `POST /api/admin/projects/{repo}/context` | Manually upsert additional context into Pinecone for a specific repo |

**Storage:** Azure Table Storage for gallery, reading list, and rate-limit counters; falls back to in-process memory when the connection string is absent (handy for local development).

**Rate limiting:** 12 requests / 60 s per visitor fingerprint (IP + User-Agent). Persisted in Azure Table `RateLimits`.

---

## Tech stack

| Layer | Technologies |
|---|---|
| Frontend | Vue 3, Vite, Tailwind CSS v4, Vue Router, markdown-it |
| Backend | Python 3.11, FastAPI, Pydantic |
| AI / Search | Google Gemini (`gemini-flash-lite`), Pinecone (`multilingual-e5-large` embeddings, `pinecone-rerank-v0`) |
| Storage | Azure Table Storage |
| Deployment | Azure Functions V2 (backend), Azure Static Web Apps or equivalent (frontend) |

---

## Running locally

```bash
# 1. Copy env files and fill in keys
cp .env.example .env
cp backend/.env.example backend/.env

# 2. Frontend
npm install
npm run dev          # http://localhost:5173

# 3. Backend (separate terminal)
cd backend
python -m uvicorn app:app --reload   # http://localhost:8000
```

Run backend tests:
```bash
cd backend
python -m pytest tests/
```

Seed the topic-gate index (one-time setup, requires `PINECONE_API_KEY`):
```bash
cd backend
python scripts/seed_questions.py
```

---

## Repository structure

```
portfolio/
├── src/                        # Vue 3 frontend
│   ├── components/             # Layout, ChatBox, Nav components
│   ├── views/                  # Page-level components
│   ├── router/index.js
│   └── data/                   # Static fallbacks (projects.json, reading.json)
├── backend/
│   ├── app.py                  # FastAPI application (local dev entry point)
│   ├── function_app.py         # Azure Functions V2 wrapper
│   ├── scripts/
│   │   └── seed_questions.py   # Seeds the Pinecone topic-gate index
│   └── src/
│       ├── config/             # Settings, logging
│       ├── routes/             # chat, projects, gallery, reading, resume, admin
│       ├── services/           # BotService, PineconeService, GitHubService, ...
│       └── models/schemas.py
└── .github/
    ├── project.json            # Portfolio metadata consumed by the backend API
    └── context.json            # Ready-to-POST body for the manual context upsert endpoint
```

---

## Admin endpoints

All admin routes require an `x-admin-key` header matching `ADMIN_API_KEY`.

**Manually upsert project context** (useful when the README alone isn't enough):
```bash
curl -X POST https://<your-api>/api/admin/projects/portfolio/context \
  -H "Content-Type: application/json" \
  -H "x-admin-key: $ADMIN_API_KEY" \
  -d @.github/context.json
```

**Flush the resume cache** (after updating the PDF):
```bash
curl -X DELETE https://<your-api>/api/admin/resume/cache \
  -H "x-admin-key: $ADMIN_API_KEY"
```
