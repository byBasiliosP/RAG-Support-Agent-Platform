# Repository Guidelines

## Project Structure & Module Organization
- `new-support-app/` hosts the Next.js frontend. Source lives in `new-support-app/src/` with routes in `src/app/`, shared UI in `src/components/`, and hooks/contexts in their respective folders. Static assets are in `new-support-app/public/`.
- `support-app-backend/` contains the FastAPI backend. Core code is under `support-app-backend/app/` with routers in `app/routers/` and integrations in `app/services/`.
- Root-level scripts (`start-dev.sh`, `stop-dev.sh`, `integration_test_*.sh`, `test_*.{py,js,sh}`) support local orchestration and integration checks.
- Avoid editing generated or vendor directories like `node_modules/`, `support-app-backend/venv/`, and cache folders.

## Build, Test, and Development Commands
- Full stack (Docker): `./start-dev.sh` starts all services via `docker-compose.dev.yml`; `./stop-dev.sh` stops them.
- Frontend:
  - `cd new-support-app && npm run dev` (local dev server)
  - `cd new-support-app && npm run build` (production build)
  - `cd new-support-app && npm run lint` (ESLint checks)
- Backend:
  - `cd support-app-backend && pip install -r requirements.txt`
  - `cd support-app-backend && uvicorn main:app --reload --port 9000`

## Coding Style & Naming Conventions
- Frontend: TypeScript + React. Prefer PascalCase for components, camelCase for variables/hooks, and keep route files in `src/app/` (`page.tsx`, `layout.tsx`). Run `npm run lint` before PRs.
- Backend: Python with PEP 8 style (4-space indentation, snake_case). Keep API routes in `app/routers/` and service logic in `app/services/`.

## Testing Guidelines
- There is no single test runner; use the ad-hoc scripts:
  - Shell integration: `./integration_test_final.sh`, `./test_complete_workflow.sh`
  - Python checks: `python test_integration.py`, `python test_enhanced_features.py`
  - Node checks: `node test_hyperlinks.js`, `node test_connection.js`
- Test files follow `test_*.{py,js,sh}` naming at the repo root.

## Commit & Pull Request Guidelines
- No Git history is available in this checkout, so no established commit convention exists. Use concise, imperative messages (e.g., `frontend: refine chat UI`, `backend: fix rag query`).
- PRs should include a brief summary, key files touched, test commands run with results, and screenshots for UI changes. Note any `.env` or configuration updates explicitly.

## Configuration & Secrets
- Local configuration is stored in `.env` at the repo root (and referenced by scripts). Never commit real API keys; document required variables instead.
