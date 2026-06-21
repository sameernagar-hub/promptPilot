# PromptPilot

PromptPilot is a full-stack prompting workspace that turns a messy request into a clearer, platform-aware prompt. It starts with a clean user session, confirms the domain when needed, asks or skips clarifying questions, generates prompt variants, scores them, and explains the recommended version in plain language.

Project owner: Sameer Nagar

Core promise:

> Understand how you prompt. Then help you ask every AI system better.

## Current Status

Phase 15 is complete. PromptPilot is ready for Phase 16 production-first Vercel deployment after cleanup, documentation, output polish, backend knowledge/RAG/DSPy support hardening, optional agent tracks, responsive QA, and final local verification.

The active local contract is intentionally simple:

- Frontend: `http://localhost:3000` or `http://127.0.0.1:3000`
- API: `http://localhost:8000` or `http://127.0.0.1:8000`
- No extra preview ports are part of the default local workflow.

## Architecture

- `apps/web`: Next.js 16, React 19, TypeScript, Tailwind CSS, Base UI, and lucide-react.
- `apps/api`: FastAPI, SQLAlchemy, Pydantic, pgvector, LiteLLM/DSPy-ready dependencies, and Uvicorn.
- `packages/shared`: shared TypeScript types and package boundary for future cross-app contracts.
- `infra/docker-compose.yml`: local Postgres with pgvector.
- `execution-reports/`: phase logs, status notes, and verification history.

The frontend reads the API URL from `NEXT_PUBLIC_API_BASE_URL`. The API reads CORS origins from `ALLOWED_ORIGINS`.

## Local Setup

Install JavaScript dependencies:

```powershell
pnpm.cmd install
```

Install or sync Python dependencies:

```powershell
uv --directory apps/api sync
```

Start local Postgres:

```powershell
docker compose -f infra/docker-compose.yml up -d
```

Create local environment files from the examples:

```powershell
Copy-Item .env.example .env
Copy-Item apps/api/.env.example apps/api/.env
Copy-Item apps/web/.env.example apps/web/.env.local
```

Start the API:

```powershell
pnpm.cmd run dev:api
```

Start the web app in a second terminal:

```powershell
pnpm.cmd run dev:web
```

## Environment Variables

Root and API:

- `APP_ENV`: `development` locally, `production` on Vercel.
- `DATABASE_URL`: Postgres connection string.
- `LLM_PROVIDER`: `ollama` for local evaluation, or a hosted provider for production.
- `OLLAMA_BASE_URL`: local Ollama endpoint for development scoring.
- `DEFAULT_MODEL`: default scoring/model identifier.
- `ALLOWED_ORIGINS`: comma-separated frontend origins. Locally this should stay on port `3000`.

Web:

- `NEXT_PUBLIC_API_BASE_URL`: API base URL. Locally this should stay on port `8000`.

Production secrets should live in Vercel or the managed provider dashboard, never in committed files.

## Main Workflows

- Start a session with display name, primary AI platform, and rules acceptance.
- Enter a raw request and choose Refine or Quick mode.
- Optionally choose a guided track: Fix, Build, Learn, Write, Compare, or Research. Tracks only tune normal preferences and add a session metadata hint; users can still edit all settings.
- Confirm or correct the detected domain when prompted.
- Answer, skip, or revise clarifying questions.
- Review the recommended platform-aware prompt first, with alternatives secondary.
- Expand evaluation details only when needed: score breakdowns, platform fit, modification audit trails, skipped-question assumptions, matched rules, trait alignment, optimization paths, recommended actions, and scorer metadata.
- Save prompts to the library, export session data, or delete session-scoped data.
- Import previous AI chats, review redacted previews, reprocess imports, and refresh the prompting profile.
- Ask profile questions and correct or hide derived profile observations.

## API Surface

Core endpoints:

- `GET /health`
- `POST /sessions`
- `GET /sessions/{session_id}`
- `POST /sessions/{session_id}/end`
- `GET /sessions/{session_id}/audit-logs`
- `GET /sessions/{session_id}/export`
- `DELETE /sessions/{session_id}/data`
- `POST /sessions/{session_id}/run-pipeline`
- `POST /sessions/{session_id}/domain-confirmation`
- `POST /sessions/{session_id}/run-prompt`
- `POST /prompts/{prompt_id}/save`
- `GET /saved-prompts`
- `GET /profile`
- `GET /profile/insights`
- `POST /profile/questions`
- `POST /profile/refresh`
- `GET /profile/export`
- `DELETE /profile/data`
- `PATCH /profile/observations/{observation_id}`
- `DELETE /profile/observations/{observation_id}`
- `POST /imports`
- `GET /imports`
- `GET /imports/{import_id}`
- `POST /imports/{import_id}/reprocess`
- `DELETE /imports/{import_id}`

## Data and Privacy

The local MVP stores sessions, prompts, scores, audit events, imports, profile traits, and derived observations in Postgres. Session exports are available as Markdown or JSON. Session deletion removes session-scoped prompts, scores, revisions, saved prompts, embeddings, and audit events, then records a non-sensitive deletion completion event. Profile reset clears derived profile data while preserving source sessions and imports.

Imported chat content is normalized and redacted for obvious secrets such as API keys, bearer tokens, emails, and phone numbers before preview.

## Verification

Run the core checks before Phase 16 deployment work:

```powershell
uv --directory apps/api run python -m compileall app
pnpm.cmd --dir apps/web lint
pnpm.cmd --dir apps/web build
```

For a local production-build smoke check, stop the dev server first and reuse the same frontend port:

```powershell
pnpm.cmd --dir apps/web start
```

## Deployment Path

Phase 16 deploys the final FastAPI API and final Next.js web app directly to Vercel from this monorepo. Use separate Vercel projects for `apps/api` and `apps/web` unless a single Vercel service setup is explicitly selected later.

Deployment is production-first:

- API project root: `apps/api`
- Web project root: `apps/web`
- API deploy command: `vercel deploy --prod`
- Web deploy command: `vercel deploy --prod`
- Web production env: `NEXT_PUBLIC_API_BASE_URL`
- API production env: `APP_ENV=production`, `DATABASE_URL`, `LLM_PROVIDER`, `DEFAULT_MODEL`, provider API keys, and the final production web origin in `ALLOWED_ORIGINS`

Do not rely on local Docker, local Ollama, localhost URLs, or preview ports for public traffic.
