# Personal Portfolio - Ikeoluwa Oladele

A personal portfolio site with a context-aware AI chatbot built into every page. The frontend is a Vue 3 SPA; the backend is a Python FastAPI service deployed on Azure App Service for Containers that handles chat, project data, resume parsing, and a small gallery.

Live: <!-- add your URL here -->  
Source: [github.com/TheBluCoder/portfolio](https://github.com/TheBluCoder/portfolio)

---

## How the chatbot works

The chat panel on every page is backed by a retrieval-augmented generation pipeline:

1. **Topic gate** - Before doing anything expensive, the query is scored against a Pinecone index seeded with representative questions. Low-scoring queries are rejected with a polite portfolio-only reply.
2. **Retrieval** - If the query passes the gate, the backend searches a Pinecone index containing chunked README and project metadata from tagged portfolio repositories.
3. **Generation** - The best retrieved context is sent to Google Gemini (`gemini-flash-lite`) to generate a grounded response.

The chat is project-aware: when a visitor is viewing a specific project, the bot can answer in that project's context.

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
| `POST /api/chat` | Topic-gated RAG chat pipeline |
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

Seed the topic-gate index:

```bash
cd backend
python scripts/seed_questions.py
```

---

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
