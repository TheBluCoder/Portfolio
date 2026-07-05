# Personal Portfolio - Recruiter Context

## What this project is

This repository powers Ikeoluwa Oladele's personal portfolio site. It is intentionally more than a static portfolio: it is a full-stack application that combines frontend presentation, backend APIs, AI-assisted retrieval, cloud persistence, and deployment automation.

The idea behind the project is simple: if a portfolio is supposed to represent engineering ability, then the portfolio itself should be engineered thoughtfully. Instead of presenting only project cards and screenshots, this site exposes a richer system that can answer questions about the work, ingest updates from GitHub, and demonstrate practical architectural tradeoffs.

## Core user-facing features

- A Vue 3 single-page application for browsing projects, gallery content, and resume information
- A context-aware AI chatbot embedded into the interface
- Live or near-live project metadata pulled from GitHub-backed sources
- A poem gallery with likes and moderated comments
- A reading list feature
- Resume parsing from a hosted PDF into structured UI data

## Why the project is technically interesting

The strongest part of the project is the combination of traditional full-stack web engineering with an intentionally scoped AI retrieval pipeline.

Instead of treating the chatbot as a novelty, the backend introduces constraints and structure:

- a Gemini resolver decides whether the latest message belongs in the portfolio domain
- the resolver rewrites valid follow-ups into standalone questions before retrieval
- repository and manual context are normalized into vector-searchable documents
- GitHub webhook ingestion keeps portfolio context synchronized with source repositories
- retrieval results are scoped to the portfolio domain before Gemini is asked to answer

This makes the chatbot closer to a product feature than a toy demo.

## Architecture overview

### Frontend

The frontend is a Vue 3 application built with:

- Vue 3
- Vite
- Tailwind CSS v4
- Vue Router
- Pinia
- markdown-it

The frontend is responsible for:

- route-driven page presentation
- project browsing and selection
- chat UI state
- admin views for some backend-powered maintenance tasks
- graceful fallback behavior when backend data is unavailable

Important frontend areas:

- `src/views/` contains route-level pages such as home, project, gallery, resume, and admin views
- `src/components/` contains reusable interface pieces including the chat box
- `src/stores/portfolio.js` centralizes portfolio project data loading and state
- `src/router/index.js` defines navigation structure

### Backend

The backend is a FastAPI application packaged as a Docker container and deployed to Azure App Service for Containers.

The backend is responsible for:

- chat API orchestration
- chat relevance resolution and context retrieval
- GitHub project ingestion
- resume parsing
- gallery CRUD and moderation
- reading-list APIs
- admin utilities
- health checks and runtime traceability

Important backend areas:

- `backend/app.py` wires the FastAPI app, CORS, logging, and router inclusion
- `backend/src/routes/` contains HTTP entrypoints
- `backend/src/services/` contains the actual business logic and integrations
- `backend/src/config/` contains runtime settings and logging setup
- `backend/tests/` contains unit tests for backend services

## Chatbot architecture

The chatbot is a retrieval-augmented generation system designed specifically for portfolio questions.

### Request flow

1. A browser request hits `POST /api/chat`
2. The request is rate-limited
3. A Gemini resolver checks whether the latest message is relevant to Ikeoluwa's portfolio and work
4. If relevant, the resolver rewrites the message as a standalone question, especially for follow-ups such as "how was it implemented?"
5. The retrieval layer queries Pinecone for relevant project context using the standalone question
6. The best context is sent back to Gemini
7. Gemini produces the final grounded answer returned to the frontend

### Why the chat uses a Gemini resolver

The chat originally used a Pinecone topic gate seeded with representative allowed questions. In practice, that design had two issues:

- raw vector similarity was too permissive for binary allow/block decisions
- Pinecone reranking improved accuracy, but the monthly free rerank quota was much tighter than Gemini's daily request quota

The current resolver-first design spends a small Gemini call up front to decide relevance and resolve follow-ups. This creates a clearer product behavior:

- irrelevant requests stop before Pinecone retrieval
- valid follow-ups become standalone questions before retrieval
- Pinecone is used for portfolio context search, not for conversational relevance classification

The tradeoff is latency. Relevant questions usually require three network steps: resolver, retrieval, and final answer generation. For a portfolio chatbot, this was considered a better tradeoff than spending scarce Pinecone rerank requests on every gate check.

### Latency and quota optimizations

The chat pipeline went through several targeted optimizations driven by two hard constraints: 500 Pinecone reranking calls per month and 500 Gemini generation requests per day.

**Parallel resolver and retrieval**

In the original sequential design, the resolver had to finish before Pinecone retrieval could start. For every relevant question, users waited the full resolver round trip before any retrieval work began.

The resolver and Pinecone fetch now run concurrently. Retrieval starts immediately using the raw question as a proxy query. Once the resolver returns, its rewritten standalone question is used for the single reranking step. If the resolver marks the query off-topic, the fetched candidates are discarded without ever calling the reranker. This removes the resolver wait on the happy path and wastes zero rerank calls on off-topic queries.

**Single rerank call per message**

The original retrieval design called the Pinecone reranker once per namespace. With multiple indexed repositories, every message consumed N rerank calls. At five namespaces that is roughly 100 user messages before the monthly quota runs out.

The retrieval layer now performs all namespace queries in parallel without reranking, merges the candidate pool into one flat list, and fires exactly one rerank call on the merged result. Quota cost is one rerank call per relevant message regardless of how many repositories are indexed.

**Namespace and host caching**

Every retrieval call previously asked Pinecone for the list of active namespaces and resolved the index host URL. These values are stable between repository additions.

The index host URL is now cached in memory after the first lookup. The namespace list is cached with a configurable TTL (default five minutes) and invalidated immediately when a write operation changes the namespace set. This removes two redundant control-plane calls per chat request.

**Response streaming**

The original design waited for the full Gemini response before sending anything to the browser. For typical responses that meant several seconds of silence.

The backend now streams the Gemini response token by token using FastAPI `StreamingResponse`. The frontend reads the response body incrementally and appends tokens as they arrive. Users see the first words within roughly 500ms instead of waiting for full generation to complete.

### Context awareness

The chat experience is not only global. When the user is on a project page, the frontend can tell the chat layer which project is active. That creates a more useful experience for questions like:

- "How did you build this?"
- "What was the hardest part?"
- "What stack did you use here?"

## GitHub ingestion design

One of the most important backend ideas is that the portfolio should not require large amounts of duplicated manual content.

### Ingestion sources

The backend can ingest:

- GitHub repository README content
- `.github/project.json` metadata inside project repositories
- manually provided supplementary context through an admin endpoint

### Namespace strategy

Each project gets a normalized repository namespace in Pinecone.

Manual context is intentionally kept in a separate namespace suffix rather than merged blindly into the same namespace. That design avoids a specific failure mode: automatic re-ingestion should not wipe hand-written supplemental notes.

This is one of the project's better examples of operational thinking. It is not just "store text in a vector DB"; it is "store it in a way that preserves the authoring workflow over time."

### Why this matters

This design reduces maintenance burden. If a project README changes, the portfolio can re-ingest it. If there is context that does not belong in a public README, it can still be added safely through a separate admin pathway.

## Resume pipeline

The resume feature is also backend-driven.

Flow:

- a resume PDF is hosted externally
- the backend downloads and extracts text with `pdfplumber`
- Gemini turns the extracted text into structured JSON
- the result is cached so the resume endpoint does not repeatedly redo the full parsing flow

This feature demonstrates:

- document processing
- LLM-based structuring
- caching and invalidation via admin endpoint

## Gallery and reading features

The site is not only project-driven.

### Gallery

The gallery supports:

- viewing poems
- likes
- comments
- moderation workflows for comment approval

### Reading list

The reading feature exposes:

- current reading state
- recently completed items
- admin CRUD routes

### Storage approach

These features use Azure Table Storage where configured, but the backend also contains local/in-memory fallback behavior for development scenarios. That gives the codebase a smoother local development story without forcing cloud dependencies for every local test.

## Deployment architecture

### Current hosting choice

The backend is currently targeted at Azure App Service for Containers.

### Why App Service for Containers was chosen

The deployment path originally explored Azure Container Apps, but there was a practical constraint: the available school-managed Azure environment made identity-based automation more difficult because Microsoft Entra access was limited.

App Service for Containers offered a simpler automation path:

- Docker image built in GitHub Actions
- image pushed to GitHub Container Registry
- deployment performed using Azure Web App publish-profile credentials

That tradeoff favored reliability and maintainability over platform elegance.

### Why not use a VM

A VM would have made SSH-style deployment straightforward, but it would also have introduced additional operational burden:

- reverse proxy setup
- patching and maintenance
- more networking and firewall management
- more day-two ops work for a portfolio project

The project deliberately avoids turning deployment into a full infrastructure hobby project unless there is a good reason.

### CI/CD flow

The GitHub Actions workflow for the backend is designed to:

- run backend tests
- build the backend Docker image
- push the image to GitHub Container Registry
- deploy the image to Azure Web App

This gives the project a credible CI/CD story that is relevant for backend or DevOps-oriented conversations.

## Security and operational boundaries

This project handles several categories of configuration and secrets, but the repository is intended to avoid storing actual secret values.

Examples of sensitive categories:

- Google API keys
- Pinecone API keys
- GitHub webhook secrets
- admin keys
- Azure storage connection strings

The architecture and metadata can describe these configuration needs without publishing the values themselves.

Other noteworthy operational choices:

- CORS is environment-driven
- request logging and request IDs help trace backend issues
- webhook requests are signature-verified
- admin routes require an admin key

## Tradeoffs and design decisions recruiters may ask about

### "Why build an AI chatbot into a portfolio?"

Because it turns a passive site into an interactive explanation layer. It also demonstrates how AI can be integrated as part of a product rather than used only as a gimmick.

### "Why use retrieval instead of just prompting Gemini with a system prompt?"

Prompt-only approaches drift too easily and require the model to infer too much from a static instruction. Retrieval grounds answers in actual project material and scales better as portfolio content grows.

### "Why use Pinecone?"

Because the project needs a persistent vector retrieval layer with namespace separation, document chunking, and a straightforward API for similarity-based retrieval. Pinecone fit the project's scope well.

### "Why use FastAPI?"

FastAPI is a good fit for a backend that needs:

- typed request/response models
- fast iteration
- async-friendly IO
- structured APIs

It keeps the backend lightweight while still supporting clean service boundaries.

### "Why deploy on App Service instead of Container Apps?"

Because the priority was having a dependable automated deploy path under the actual Azure account constraints available at the time. App Service for Containers provided a better path for that than the blocked identity-based setup for Container Apps.

### "Why not just keep all project information static in the frontend?"

Because that would make the portfolio harder to maintain and weaken the chatbot's grounding. Pulling from GitHub-backed sources allows project context to stay closer to the source of truth.

### "How do you prevent manual context from being lost?"

By storing it in a separate namespace instead of mixing it into the normal repository ingestion namespace.

### "What are the weakest points in the system?"

The most fragile areas are usually infrastructure and external dependencies:

- cloud plan and quota constraints
- registry auth and deployment integration
- third-party API availability
- keeping environment configuration consistent across local and deployed environments

### "What would you improve next?"

Reasonable next steps include:

- stronger deployment observability
- more formal integration tests
- richer project ingestion summaries
- better admin tooling for manual context and ingestion visibility
- more polished public documentation around architecture diagrams and hosting

## Suggested mental model for this project

This repository is best understood as a combination of:

- portfolio site
- AI-backed retrieval product
- backend integration layer
- small deployment platform

Its value is not only in any one feature. The value is in how the pieces fit together:

- frontend state and routing
- backend API design
- retrieval and generation workflow
- metadata ingestion
- persistence
- deployment automation

That combination makes it a strong interview artifact for discussions about backend engineering, full-stack architecture, applied AI, and practical DevOps tradeoffs.
