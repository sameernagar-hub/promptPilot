# Phase 8: Prompting Trait Detection

## Goal

Analyze sessions and imported chats to recognize how the user prompts.

The system should detect useful patterns without sounding judgmental. Traits should be explainable and backed by evidence.

## Status

Complete.

## Planned Pipeline

```txt
collect prompt/session/chat examples
-> normalize examples
-> extract behavioral signals
-> map signals to prompting traits
-> calculate confidence
-> store evidence snippets
-> update the user prompting profile
```

## Initial Traits

- Whether prompts usually include enough context.
- Whether prompts state a clear outcome.
- Whether constraints, audience, format, or success criteria are missing.
- Whether the user prefers direct, friendly, technical, formal, or informal language.
- Whether the user tends to ask for short answers, deep reasoning, tables, plans, or checklists.
- Whether the user under-specifies domain, environment, tools, or audience.
- Whether sensitive domains need stronger safety boundaries.

## Planned Work

- [x] Implement deterministic first-pass trait extraction from `problem_sessions`.
- [x] Add trait scoring and confidence rules.
- [x] Store evidence references that point back to sessions or imported messages.
- [x] Add profile refresh behavior after new prompt activity.
- [x] Make trait labels and explanations user-facing.

## Verification

- [x] Trait detection runs on existing sessions.
- [x] Each trait has a score, confidence, and evidence.
- [x] Profile output refreshes after new activity.
- [x] Low-evidence traits are marked as tentative.
- [x] The system does not claim patterns without enough data.

## Implementation Notes

- Added `prompting_trait_signals` as the per-example signal layer under aggregate trait observations.
- Replaced the aggregate-only profile analyzer with `trait_detector_v1`.
- Normalized local sessions and imported user messages into one example stream.
- Extracted signals for context depth, goal clarity, constraints, domain precision, format, tone, formality, iteration style, risk awareness, source expectation, technical depth, and missing context.
- Aggregated signals into observations with evidence level: `none`, `tentative`, `emerging`, or `strong`.
- Added representative signals to profile API responses.
- Updated `/profile` to show evidence level badges, signal counts, and signal explanations.

## Verification Notes

- Docker/Postgres was running and accepted API requests.
- DB-backed smoke test passed:
  - `GET /health` returned `200` with database `ok`.
  - `POST /sessions` returned `201`.
  - `POST /sessions/{id}/run-pipeline` returned `200`.
  - `POST /profile/refresh` returned `200` with 12 observations and 176 signals in the tested local database.
  - `GET /profile` returned `200`.
  - `prompting_trait_signals` table exists.
- `uv run python -m compileall app` passed from `apps/api`.
- SQLAlchemy mapper configuration passed and registered 20 ORM tables.
- `uv --directory apps/api run python main.py` passed.
- `pnpm.cmd --dir apps/web lint` passed.
- `pnpm.cmd --dir apps/web build` passed.
- In-app Browser was unavailable, so local Microsoft Edge Playwright fallback verified `/profile` rendered 12 trait cards, evidence badges, and signal text.
