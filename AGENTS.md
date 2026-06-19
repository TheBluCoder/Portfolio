# Repository Guidelines

## Project Structure & Module Organization

This repository contains a Vue 3/Vite portfolio frontend with a Python API backend.

- `src/` holds frontend code: `views/` for routed pages, `components/` for reusable Vue components, `components/ui/` for shared UI primitives, `router/`, `stores/`, `data/`, `lib/`, and `assets/`.
- `public/` stores static files served directly, including `portrait.jpg` and favicons.
- `backend/` contains the FastAPI/Azure Functions backend. Entry points are `backend/app.py` and `backend/function_app.py`; routes, services, models, and config live under `backend/src/`.

## Build, Test, and Development Commands

- `npm install` installs frontend dependencies from `package-lock.json`.
- `npm run dev` starts the Vite dev server.
- `npm run build` creates the production frontend bundle.
- `npm run preview` serves the production build locally.
- `npm run lint` runs ESLint and applies automatic fixes.
- `npm run format` runs Prettier on `src/`.
- `cd backend && pip install -r requirements.txt` installs backend dependencies.
- `cd backend && uvicorn app:app --reload` starts the backend at `http://localhost:8000`.

## Coding Style & Naming Conventions

Use 2-space indentation for JavaScript, Vue, CSS, and related frontend files. Follow `.editorconfig`: UTF-8, LF line endings, final newline, trimmed trailing whitespace, and 100-character max lines. Prettier uses single quotes and no semicolons.

Name Vue components in PascalCase, such as `ChatBox.vue` and `ResumeView.vue`. Keep JSON content files lowercase, such as `projects.json`. Backend Python modules currently mix lowercase and PascalCase; prefer lowercase `snake_case.py` for new modules unless extending an existing pattern.

## Testing Guidelines

No automated test script is currently defined in `package.json`, and no dedicated test directory is present. For now, run `npm run lint`, `npm run build`, and manually exercise affected pages with `npm run dev`. For backend changes, start `uvicorn app:app --reload` and verify endpoints through `http://localhost:8000/docs`.

When adding tests, colocate frontend tests near the component or create a clear `tests/` directory, and use descriptive names like `ChatBox.spec.js` or `test_chat_routes.py`.

## Commit & Pull Request Guidelines

Recent commits are short and descriptive, for example `experience.json` and `updates the readme`. Use concise imperative commit messages that name the changed area, such as `update project data` or `fix chat route error`.

Pull requests should include a brief summary, testing performed, linked issue when applicable, and screenshots for visible frontend changes. Note any required environment variables or backend setup steps.

## Security & Configuration Tips

Do not commit real secrets. Use root `.env.example` and `backend/.env.example` as templates, then keep credentials in ignored `.env` files.
