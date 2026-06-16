# Phase 3: Backend API Skeleton

## Goal

Build the first FastAPI service.

## Status

Complete.

## Prerequisites

- Python 3.10+ available.
- uv project initialized.
- Backend dependencies installed.

## Planned Modules

```txt
apps/api/
  app/
    main.py
    config.py
    db.py
    models.py
    schemas.py
    services/
      classifier.py
      question_generator.py
      prompt_generator.py
      prompt_scorer.py
      llm_client.py
    routers/
      sessions.py
      prompts.py
      health.py
```

## Implemented Modules

- `apps/api/app/config.py`
- `apps/api/app/db.py`
- `apps/api/app/models.py`
- `apps/api/app/schemas.py`
- `apps/api/app/services/classifier.py`
- `apps/api/app/services/question_generator.py`
- `apps/api/app/services/prompt_generator.py`
- `apps/api/app/services/prompt_scorer.py`
- `apps/api/app/services/llm_client.py`
- `apps/api/app/routers/health.py`
- `apps/api/app/routers/sessions.py`
- `apps/api/app/routers/prompts.py`

## Initial Endpoint Plan

- `GET /health`
- `POST /sessions`
- `GET /sessions/{session_id}`
- `POST /sessions/{session_id}/classify`
- `POST /sessions/{session_id}/questions`
- `POST /sessions/{session_id}/answers`
- `POST /sessions/{session_id}/generate-prompts`
- `POST /sessions/{session_id}/score-prompts`
- `POST /sessions/{session_id}/run-prompt`
- `POST /prompts/{prompt_id}/save`
- `GET /saved-prompts`

## First Implementation Style

- Start with simple rule-based logic.
- Keep service boundaries clear so DSPy and retrieval can replace rules later.
- Use Pydantic schemas for request and response contracts.

## Verification

- [x] `GET /health` returns a healthy response.
- [x] Session creation works.
- [x] Classifier returns domain, intent, and risk.
- [x] Clarifying question generation works.
- [x] Prompt generation returns at least 3 variants.
- [x] Scorer returns dimensions and total score.

## Execution Notes

Date: 2026-06-15

- Added the first FastAPI service skeleton with router/service/schema boundaries.
- Added config loading for database and local model settings.
- Added a database health probe using `DATABASE_URL`.
- Added an in-memory session/prompt/saved-prompt store.
  - Note: SQLAlchemy persistence and real database models remain Phase 4 work.
- Added rule-based classification for initial MVP domains and intents.
- Added clarifying question generation by domain and risk level.
- Added prompt variant generation with three strategies:
  - `diagnostic`
  - `beginner_step_by_step`
  - `expert_consultant`
- Added prompt scoring dimensions:
  - `clarity`
  - `specificity`
  - `safety`
  - `actionability`
  - `domain_fit`
  - `beginner_friendliness`
  - `expected_answer_quality`
- Added a Phase 3 `run-prompt` stub that returns provider/model metadata without calling Ollama yet.
- Added save/list prompt endpoints backed by the in-memory store.
- Verified the full endpoint flow with FastAPI `TestClient`.
  - `GET /health` returned `200` with database status `ok`.
  - `POST /sessions` returned `201`.
  - `POST /sessions/{session_id}/classify` returned domain, intent, and risk.
  - `POST /sessions/{session_id}/questions` returned clarifying questions.
  - `POST /sessions/{session_id}/answers` recorded answers.
  - `POST /sessions/{session_id}/generate-prompts` returned 3 variants.
  - `POST /sessions/{session_id}/score-prompts` returned scored variants and a recommendation.
  - `POST /sessions/{session_id}/run-prompt` returned the Phase 3 run stub.
  - `POST /prompts/{prompt_id}/save` saved a prompt.
  - `GET /saved-prompts` returned the saved prompt.
- Verification note:
  - FastAPI emitted a `StarletteDeprecationWarning` from `TestClient` recommending `httpx2`; the endpoint flow still passed.
- Started the local API dev server with Uvicorn.
  - URL: `http://127.0.0.1:8000`
  - Verified `GET /health` over HTTP returned status `ok` and database status `ok`.
