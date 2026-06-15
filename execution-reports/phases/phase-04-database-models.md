# Phase 4: Database Models

## Goal

Store sessions, prompts, scores, and future prompt sources.

## Status

Not started.

## Prerequisites

- Database service running.
- SQLAlchemy configured.
- Migration strategy selected.

## Core Tables

- `users`
- `problem_sessions`
- `clarifying_questions`
- `prompt_variants`
- `prompt_scores`
- `saved_prompts`
- `prompt_sources`
- `prompt_embeddings`
- `domain_packs`

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

- [ ] Models match API needs.
- [ ] Relationships are defined.
- [ ] JSON fields are used where helpful for settings and score breakdowns.
- [ ] pgvector field strategy is decided before embeddings are implemented.
