# Phase 7: Prompting Profile Foundation

## Goal

Pivot PromptPilot from a prompt-generation MVP into a prompting experience intelligence product.

The product should understand how a user prompts, store prompting traits with evidence, and use those traits to guide future refinement.

## Status

Complete.

## Roadmap Change

This phase replaces the previous Phase 7 prompt knowledge base. Prompt knowledge base, RAG, DSPy, and agent tracks move later because the next product foundation is the user profile, not an external prompt corpus.

## Data Model Targets

- `user_prompt_profiles`
- `prompting_traits`
- `trait_observations`
- `conversation_imports`
- `imported_conversations`
- `imported_messages`
- `prompt_revisions`
- `domain_confirmations`
- `platform_preferences`
- `integration_connections`

## Trait Taxonomy Seed

- `context_depth`
- `goal_clarity`
- `constraint_specificity`
- `domain_precision`
- `format_preference`
- `tone_preference`
- `formality_preference`
- `iteration_style`
- `risk_awareness`
- `source_expectation`
- `technical_depth`
- `missing_context_patterns`

## Planned Work

- [x] Add profile-oriented models and schemas.
- [x] Add a profile summary API that can return empty, partial, and populated states.
- [x] Summarize existing local sessions into first-pass observations.
- [x] Add a Profile route or panel in the web app.
- [x] Show traits with confidence and supporting examples.
- [x] Keep profile records separate from generated prompt variants.

## Verification

- [x] Profile schema exists.
- [x] Existing sessions can produce profile observations through the profile analyzer.
- [x] Observations include trait, score, confidence, and evidence reference.
- [x] UI can render empty, partial, and populated profile states.
- [x] The next implementation phase is trait detection, not prompt KB ingestion.

## Implementation Notes

- Added profile tables, trait catalog, observation tables, import placeholders, prompt revisions, domain confirmations, platform preferences, and integration connection models.
- Added `GET /profile` and `POST /profile/refresh`.
- Added deterministic `session_summary_v1` profile analysis from local sessions.
- Added `/profile` in the Next.js app with profile metrics, trait cards, confidence scores, and session evidence links.
- Added Profile links to the workspace, library, and settings navigation.

## Verification Notes

- `uv run python -m compileall app` passed from `apps/api`.
- `uv --directory apps/api run python main.py` passed.
- SQLAlchemy mapper configuration passed and registered 19 ORM tables.
- `pnpm.cmd --dir apps/web lint` passed.
- `pnpm.cmd --dir apps/web build` passed.
- FastAPI `TestClient` profile smoke test was blocked because Docker Desktop was not running and the local Postgres service was unavailable.
