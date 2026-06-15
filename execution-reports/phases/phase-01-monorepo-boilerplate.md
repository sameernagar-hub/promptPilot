# Phase 1: Create Monorepo Boilerplate

## Goal

Initialize the full-stack project structure.

## Status

Complete.

## Prerequisites

- [x] pnpm available.
- [x] Python runtime available.
- [x] uv available.
- [x] User approval to begin scaffolding.

## Planned Directory Structure

```txt
apps/
  web/
  api/
packages/
  shared/
infra/
docs/
scripts/
datasets/
  prompt-sources/
evals/
  promptfoo/
```

## Planned Root Files

- [x] `README.md`
- [x] `.env.example`
- [x] `.gitignore`
- [x] `package.json`
- [x] `pnpm-workspace.yaml`
- [x] `pnpm-lock.yaml`

## Planned Frontend Setup

- [x] Create Next.js app in `apps/web`.
- [x] Use TypeScript.
- [x] Use Tailwind CSS.
- [x] Add ESLint.
- [x] Add lucide-react, class-variance-authority, clsx, and tailwind-merge.
- [x] Initialize shadcn/ui.

## Planned Backend Setup

- [x] Create backend in `apps/api`.
- [x] Initialize uv project.
- [x] Add FastAPI, Uvicorn, Pydantic, SQLAlchemy, psycopg, pgvector, python-dotenv, LiteLLM, and DSPy.
- [x] Add minimal FastAPI app entrypoint for startup verification.

## Verification

- [x] Folder structure exists.
- [x] Frontend app starts.
- [x] Backend app starts.
- [x] Root README and env examples exist.
- [x] Changelog updated with commands and results.

## Verified Results

- Frontend lint passed with `pnpm.cmd lint:web`.
- Frontend production build passed with `pnpm.cmd build:web`.
- Frontend dev server returned HTTP `200` on `http://127.0.0.1:3000`.
- Backend import check passed with `uv --directory apps/api run python main.py`.
- Backend Uvicorn server returned HTTP `200` on `http://127.0.0.1:8000`.
- Local startup was verified at:
  - Web: `http://127.0.0.1:3000`
  - API: `http://127.0.0.1:8000`

## Do Not Start Until

Complete. Next phase is Phase 2 infrastructure.
