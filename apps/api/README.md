# PromptPilot API

FastAPI service for the PromptPilot prompt intelligence profile.

The API imports prompt sessions, normalizes and redacts messages, builds a derived prompting profile, and stores prompt intelligence reports. OpenAI is the default model provider for report analysis; deterministic scoring remains available as a local fallback when the provider is not configured.

## Local Environment

```env
APP_ENV=development
DATABASE_URL=postgresql://prompt_engine:prompt_engine@localhost:5432/prompt_engine
LLM_PROVIDER=openai
OPENAI_API_KEY=
DEFAULT_MODEL=gpt-5.5
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

`OPENAI_API_KEY` is server-only. Keep real keys in ignored `.env` files or managed production secrets.

## Run Locally

```powershell
uv --directory apps/api run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Prompt Intelligence Endpoints

Create a report directly from pasted text:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/intelligence/analyze `
  -ContentType 'application/json' `
  -Body '{"platform":"codex","source_type":"markdown","title":"Phase 16 session","raw_text":"User: Pivot this app into prompt intelligence\nAssistant: ..."}'
```

Analyze an existing import:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/intelligence/analyze `
  -ContentType 'application/json' `
  -Body '{"import_id":"<import-id>"}'
```

Report reads:

- `GET /intelligence/reports`
- `GET /intelligence/reports/latest`
- `GET /intelligence/reports/{report_id}`

## Imports and Profile

- `POST /imports`
- `GET /imports`
- `GET /imports/{import_id}`
- `POST /imports/{import_id}/reprocess`
- `DELETE /imports/{import_id}`
- `GET /profile`
- `POST /profile/refresh`
- `GET /profile/insights`
- `POST /profile/questions`
- `PATCH /profile/observations/{observation_id}`
- `DELETE /profile/observations/{observation_id}`
- `GET /profile/export?format=markdown|json`
- `DELETE /profile/data`

## Data Model

- `conversation_imports`, `imported_conversations`, and `imported_messages` store normalized prompt sessions.
- `prompting_trait_signals` and `trait_observations` store derived behavioral evidence.
- `prompt_intelligence_reports` stores the report headline, summary, style scores, behavior patterns, recommendations, next-prompt recipe, comparisons, evidence, provider, model, and metadata.
- Legacy session and prompt variant tables remain for historical data and regression tests.

## Runtime Behavior

- `LLM_PROVIDER=openai` with `OPENAI_API_KEY` uses the OpenAI Responses API for report analysis.
- Missing or failing OpenAI configuration falls back to deterministic local analysis for development stability.
- Production startup fails if `APP_ENV=production`, `LLM_PROVIDER=openai`, and `OPENAI_API_KEY` is missing.
- Production startup also rejects local database URLs, local Ollama as the production provider, and localhost CORS origins.

## Verification

```powershell
uv --directory apps/api run python -m compileall app
uv --directory apps/api run python ../../evals/promptfoo/phase14_regression.py
```
