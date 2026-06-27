# Personal Portfolio - Ikeoluwa Oladele

A personal portfolio site with a context-aware AI chatbot built into every page. The frontend is a Vue 3 SPA; the backend is a Python FastAPI service deployed on Azure App Service for Containers that handles chat, project data, resume parsing, and a small gallery.

Live: <!-- add your URL here -->  
Source: [github.com/TheBluCoder/portfolio](https://github.com/TheBluCoder/portfolio)

---

## How the chatbot works

The chat panel on every page is backed by a retrieval-augmented generation pipeline:

1. **Resolver** - A lightweight Gemini call decides whether the latest message is relevant to Ikeoluwa's portfolio. It also rewrites valid follow-ups into standalone questions.
2. **Retrieval** - If the resolver accepts the message, the backend searches a Pinecone index containing chunked README and project metadata from tagged portfolio repositories.
3. **Generation** - The best retrieved context is sent back to Gemini to generate a grounded response.

The chat is project-aware: when a visitor is viewing a specific project, the bot can answer in that project's context.

### Why Gemini resolves relevance

The chat originally used a Pinecone topic-gate index before retrieval. That was cheaper in theory, but it had two practical problems:

- Raw vector similarity was too loose for a binary allow/block decision.
- Pinecone reranking made the gate much more accurate, but the free monthly rerank allowance is much smaller than the daily Gemini request allowance.

The current design spends a small Gemini call up front to handle two jobs that vector search handled poorly: deciding whether the request belongs in the portfolio domain, and resolving conversational follow-ups like "how was it implemented?" into standalone questions. This means relevant chat requests usually take three network steps:

1. Gemini resolver for relevance and follow-up rewriting.
2. Pinecone retrieval for portfolio context.
3. Gemini generation for the final grounded answer.

That adds latency, but avoids using Pinecone rerank for every gate check and prevents irrelevant questions from reaching retrieval. The tradeoff favors correctness and predictable Pinecone usage over the absolute lowest number of network calls.

---

## Project ingestion

Every public GitHub repository tagged with the `portfolio` topic can be indexed automatically:

- A GitHub webhook fires on supported repository events.
- The backend verifies the webhook signature, fetches the repo README and optional `.github/project.json`, chunks the content, and upserts it into Pinecone.
- If a repository is deleted or made private, its namespace is removed.

Manual supplementary context can also be added through the admin API.

---

## Architecture

### Frontend (`src/`)

Vue 3, Vite, Tailwind CSS v4, Vue Router

| Component | Responsibility |
|---|---|
| `Layout.vue` | Shell; provides chat context and owns `ChatBox` state |
| `ChatBox.vue` | Chat UI; keeps per-project conversation history and renders markdown |
| `ProjectView.vue` | Fetches project data and sets active project context |

Routes: `/`, `/introduction`, `/about`, `/projects`, `/gallery`, `/resume`

### Backend (`backend/`)

Python 3.11, FastAPI, Azure App Service for Containers

The FastAPI app runs locally with Uvicorn and is packaged as a container for deployment.

| Route | Purpose |
|---|---|
| `POST /api/chat` | Gemini-resolved RAG chat pipeline |
| `GET /api/projects` | Lists portfolio repositories with merged metadata |
| `GET /api/resume` | Parses a hosted resume PDF with Gemini and caches the result |
| `GET/POST/PATCH/DELETE /api/gallery/*` | Poem, comment, and like flows |
| `GET/PUT/POST/DELETE /api/reading/*` | Reading list CRUD |
| `POST /api/github/webhook` | GitHub webhook ingestion trigger |
| `POST /api/admin/projects/{repo}/context` | Manual context upsert for a repository |

Storage:
- Azure Table Storage for gallery, reading list, and rate-limit counters
- in-process fallbacks for local development when storage is not configured

Rate limiting:
- 12 requests per 60 seconds per visitor fingerprint

---

## Tech stack

| Layer | Technologies |
|---|---|
| Frontend | Vue 3, Vite, Tailwind CSS v4, Vue Router, markdown-it |
| Backend | Python 3.11, FastAPI, Pydantic |
| AI / Search | Google Gemini, Pinecone |
| Storage | Azure Table Storage |
| Deployment | Azure App Service for Containers (backend), Vercel (frontend) |

---

## Running locally

```bash
# 1. Copy env files and fill in keys
cp .env.example .env
cp backend/.env.example backend/.env

# 2. Frontend
npm install
npm run dev

# 3. Backend (separate terminal)
cd backend
python -m uvicorn app:app --reload
```

Run backend tests:

```bash
cd backend
set PYTHONPATH=.
python -m unittest discover tests
```

## Repository structure

```text
portfolio/
|-- src/
|   |-- components/
|   |-- views/
|   |-- router/
|   `-- data/
|-- backend/
|   |-- app.py
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- scripts/
|   `-- src/
|       |-- config/
|       |-- models/
|       |-- routes/
|       `-- services/
`-- .github/
    |-- project.json
    |-- context.json
    `-- workflows/
```

---

## Admin endpoints

All admin routes require an `x-admin-key` header matching `ADMIN_API_KEY`.

Manually upsert project context:

```bash
curl -X POST https://<your-api>/api/admin/projects/portfolio/context \
  -H "Content-Type: application/json" \
  -H "x-admin-key: $ADMIN_API_KEY" \
  -d @.github/context.json
```

Flush the resume cache:

```bash
curl -X DELETE https://<your-api>/api/admin/resume/cache \
  -H "x-admin-key: $ADMIN_API_KEY"
```
