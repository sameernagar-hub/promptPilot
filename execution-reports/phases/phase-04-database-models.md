# Phase 4: Database Models

## Goal

Store sessions, prompts, scores, and future prompt sources.

## Status

Complete.

## Prerequisites

- Database service running.
- SQLAlchemy configured.
- Migration strategy selected.

## Core Tables

- [x] `users`
- [x] `problem_sessions`
- [x] `clarifying_questions`
- [x] `prompt_variants`
- [x] `prompt_scores`
- [x] `saved_prompts`
- [x] `prompt_sources`
- [x] `prompt_embeddings`
- [x] `domain_packs`

## Important Model Fields

### ProblemSession

- `id`
- `raw_input`
- `detected_domain`
- `detected_intent`
- `risk_level`
- `user_settings`
- `status`
- `created_at`
- `updated_at`

### PromptVariant

- `id`
- `session_id`
- `title`
- `strategy`
- `prompt_text`
- `recommendation_label`
- `score_total`
- `score_breakdown`
- `explanation`
- `created_at`

### PromptSource

- `id`
- `source_name`
- `source_url`
- `license`
- `raw_text`
- `normalized_text`
- `domain`
- `intent`
- `format`
- `risk_level`
- `embedding`
- `created_at`

## Verification

- [x] Models match API needs.
- [x] Relationships are defined.
- [x] JSON fields are used where helpful for settings and score breakdowns.
- [x] pgvector field strategy is decided before embeddings are implemented.

## Implementation Notes

Date: 2026-06-15

- Replaced the Phase 3 in-memory store with a SQLAlchemy-backed store.
- Added SQLAlchemy ORM models in `apps/api/app/models.py`.
- Added engine/session/bootstrap logic in `apps/api/app/db.py`.
- Added FastAPI lifespan initialization to create the local schema on startup.
- Kept the public `DATABASE_URL` format as `postgresql://...`.
  - Internally, SQLAlchemy normalizes it to `postgresql+psycopg://...` because the project uses `psycopg` v3.
- Selected the Phase 4 migration strategy:
  - Use `Base.metadata.create_all()` for local MVP bootstrapping.
  - Defer formal migration tooling such as Alembic until schema churn justifies it.
- Selected the pgvector field strategy:
  - `prompt_embeddings.embedding` uses pgvector's `vector` type.
  - Initial nullable dimension is `1536`.
  - Embedding generation itself remains future Phase 7/8 work.
- Added persisted relationships:
  - `users` to `problem_sessions`
  - `problem_sessions` to `clarifying_questions`
  - `problem_sessions` to `prompt_variants`
  - `prompt_variants` to `prompt_scores`
  - `prompt_variants` to `saved_prompts`
  - `prompt_sources` to `prompt_embeddings`
  - `prompt_variants` to `prompt_embeddings`
- Updated API routes so sessions, questions, answers, prompt variants, scores, and saved prompts persist to Postgres.

## Database Verification

- Ran `init_database()`.
  - Result: schema initialization completed successfully.
- Confirmed pgvector extension.
  - Result: `vector 0.8.2`.
- Confirmed all Phase 4 tables exist in Postgres.
  - `clarifying_questions`
  - `domain_packs`
  - `problem_sessions`
  - `prompt_embeddings`
  - `prompt_scores`
  - `prompt_sources`
  - `prompt_variants`
  - `saved_prompts`
  - `users`
- Confirmed `prompt_embeddings.embedding` uses the pgvector `vector` type.
- Ran a full API persistence smoke test.
  - `POST /sessions` created a `problem_sessions` row.
  - `POST /sessions/{session_id}/questions` created `clarifying_questions` rows.
  - `POST /sessions/{session_id}/generate-prompts` created 3 active `prompt_variants` rows.
  - `POST /sessions/{session_id}/score-prompts` created 3 `prompt_scores` rows.
  - `POST /prompts/{prompt_id}/save` created a `saved_prompts` row.
- Verified persisted row counts after the smoke test:
  - `problem_sessions`: 1
  - `clarifying_questions`: 2
  - `prompt_variants`: 3
  - `prompt_scores`: 3
  - `saved_prompts`: 1
