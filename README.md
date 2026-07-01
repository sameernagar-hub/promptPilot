# PromptPilot

PromptPilot is a prompt intelligence profile. It imports prompt sessions from Codex, Claude, ChatGPT, Cursor, Gemini, or plain Markdown, then judges what those prompts reveal about your prompting behavior.

Core promise:

> Understand how you prompt. Then improve the way you ask every AI system.

PromptPilot is no longer centered on generating or formatting prompts. The main workflow is now import, judge, explain, and improve.

Project owner: Sameer Nagar

## Current Status

Phase 15.5 is complete and the project is ready for Phase 16 final production work.

The active product surface is:

- Import or paste a `.md`, `.txt`, `.json`, or transcript-style prompt session.
- Click `Judge My Prompts`.
- Get a prompt intelligence report with style scores, evidence excerpts, behavior patterns, recommendations, platform comparisons, and a next-prompt recipe.
- Review the prompt intelligence profile and import ledger.

The old prompt generation page has been removed from active frontend routes. Legacy backend session/prompt endpoints remain for data continuity and regression coverage, but they are not the primary product path.

## Architecture

- `apps/web`: Next.js 16, React 19, TypeScript, Tailwind CSS, Base UI, and lucide-react.
- `apps/api`: FastAPI, SQLAlchemy, Pydantic, pgvector, OpenAI SDK, and Uvicorn.
- `packages/shared`: shared TypeScript package boundary.
- `infra/docker-compose.yml`: local Postgres with pgvector.
- `execution-reports/`: phase reports, status notes, and verification history.

The frontend reads `NEXT_PUBLIC_API_BASE_URL`. The API reads `DATABASE_URL`, `LLM_PROVIDER`, `OPENAI_API_KEY`, `DEFAULT_MODEL`, and `ALLOWED_ORIGINS`.

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

Set `OPENAI_API_KEY` in ignored local env files or in the production secret store. Do not commit real API keys.

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

- `APP_ENV`: `development` locally, `production` for production.
- `DATABASE_URL`: Postgres connection string.
- `LLM_PROVIDER`: defaults to `openai`.
- `OPENAI_API_KEY`: server-only OpenAI API key.
- `DEFAULT_MODEL`: defaults to `gpt-5.5`.
- `ALLOWED_ORIGINS`: comma-separated frontend origins.
- `OLLAMA_BASE_URL`: legacy local fallback setting, not the default product path.

Web:

- `NEXT_PUBLIC_API_BASE_URL`: API base URL. Locally this should stay on port `8000`.

## Main Workflows

- Import a prompt session from Markdown, JSON, plain text, or pasted transcript.
- Normalize and redact obvious secrets before previews.
- Generate a prompt intelligence report through `/intelligence/analyze`.
- Store reports in `prompt_intelligence_reports` with provider/model/status metadata.
- Ask the profile questions such as “What do I usually forget to include?” or “How should I prompt Codex better?”
- Correct or hide derived profile observations.
- Export or delete derived profile data.

## API Surface

Prompt intelligence:

- `POST /intelligence/analyze`
- `GET /intelligence/reports`
- `GET /intelligence/reports/latest`
- `GET /intelligence/reports/{report_id}`

Imports and profile:

- `POST /imports`
- `GET /imports`
- `GET /imports/{import_id}`
- `POST /imports/{import_id}/reprocess`
- `DELETE /imports/{import_id}`
- `GET /profile`
- `GET /profile/insights`
- `POST /profile/questions`
- `POST /profile/refresh`
- `GET /profile/export`
- `DELETE /profile/data`
- `PATCH /profile/observations/{observation_id}`
- `DELETE /profile/observations/{observation_id}`

Operational:

- `GET /health`

Legacy session endpoints are still present for historical data and regression checks.

## Data and Privacy

PromptPilot stores imports, normalized messages, derived traits, profile observations, prompt intelligence reports, and audit events in Postgres.

Imported content is redacted for obvious secrets such as OpenAI-style keys, bearer tokens, emails, phone numbers, and password-like fields before preview. Redaction is best-effort and does not replace careful secret handling.

Real OpenAI API keys belong only in ignored local env files or managed production secrets. If a key is ever pasted into chat, rotate it before using it in production.

## Verification

Run the core checks before Phase 16 deployment work:

```powershell
uv --directory apps/api run python -m compileall app
uv --directory apps/api run python ../../evals/promptfoo/phase14_regression.py
pnpm.cmd --dir apps/web lint
pnpm.cmd --dir apps/web build
```

## Phase 16 Path

Phase 16 should deploy the final FastAPI API and final Next.js web app with managed production environment variables.

Production API requirements:

- `APP_ENV=production`
- Managed `DATABASE_URL`
- `LLM_PROVIDER=openai`
- `OPENAI_API_KEY`
- `DEFAULT_MODEL=gpt-5.5`
- Production web origin in `ALLOWED_ORIGINS`

Production web requirements:

- `NEXT_PUBLIC_API_BASE_URL`

Do not rely on local Docker, localhost URLs, local Ollama, or unrotated exposed keys for public traffic.
