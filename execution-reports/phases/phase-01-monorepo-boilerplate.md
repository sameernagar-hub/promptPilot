# Phase 1: Create Monorepo Boilerplate

## Goal

Initialize the full-stack project structure.

## Status

Not started.

## Prerequisites

- pnpm available.
- Python runtime available.
- uv available.
- User approval to begin scaffolding.

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

- `README.md`
- `.env.example`
- `.gitignore`
- package manager/workspace files as needed

## Planned Frontend Setup

- Create Next.js app in `apps/web`.
- Use TypeScript.
- Use Tailwind CSS.
- Add ESLint.
- Add lucide-react, class-variance-authority, clsx, and tailwind-merge.
- Initialize shadcn/ui.

## Planned Backend Setup

- Create backend in `apps/api`.
- Initialize uv project.
- Add FastAPI, Uvicorn, Pydantic, SQLAlchemy, psycopg, pgvector, python-dotenv, LiteLLM, and DSPy.

## Verification

- [ ] Folder structure exists.
- [ ] Frontend app starts.
- [ ] Backend app starts.
- [ ] Root README and env examples exist.
- [ ] Changelog updated with commands and results.

## Do Not Start Until

The user gives explicit instruction to begin implementation.
