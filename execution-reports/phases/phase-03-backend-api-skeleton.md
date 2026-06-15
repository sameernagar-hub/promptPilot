# Phase 3: Backend API Skeleton

## Goal

Build the first FastAPI service.

## Status

Not started.

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

- [ ] `GET /health` returns a healthy response.
- [ ] Session creation works.
- [ ] Classifier returns domain, intent, and risk.
- [ ] Clarifying question generation works.
- [ ] Prompt generation returns at least 3 variants.
- [ ] Scorer returns dimensions and total score.
