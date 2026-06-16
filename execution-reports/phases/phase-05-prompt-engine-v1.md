# Phase 5: Prompt Engine V1

## Goal

Build the first working prompt generation pipeline.

## Status

Complete.

## Pipeline

```txt
raw problem
-> classify domain and intent
-> decide whether clarifying questions are needed
-> generate clarifying questions
-> merge answers and user settings
-> generate 3 prompt variants
-> score prompt variants
-> recommend best prompt
```

## Prompt Strategies

- `diagnostic`
- `beginner_step_by_step`
- `expert_consultant`
- `safety_first`
- `comparison`
- `questions_first`

## Prompt Tuning Settings

- `length`: short, medium, deep
- `skill_level`: beginner, practical, expert
- `tone`: direct, friendly, technical
- `format`: checklist, guide, table, conversation, plan
- `risk`: safe_only, normal, advanced
- `sources`: none, web, official_docs

## Scoring Dimensions

- clarity
- specificity
- safety
- actionability
- domain_fit
- beginner_friendliness
- expected_answer_quality

## Verification

- [x] Pipeline can run without an external LLM.
- [x] Each variant has title, strategy, prompt text, score, and explanation.
- [x] Safety-first logic appears for risky domains.
- [x] Recommended variant is selected deterministically.

## Implementation Notes

Date: 2026-06-15

- Added `apps/api/app/services/prompt_engine.py` as the first complete prompt-engine pipeline orchestrator.
- Added `POST /sessions/{session_id}/run-pipeline`.
- Added Phase 5 request/response schemas:
  - `PromptEngineRunRequest`
  - `PromptEngineRunResponse`
- Pipeline stages:
  - classify the raw problem
  - generate clarifying questions
  - merge supplied answers and user settings
  - decide whether clarification is still needed
  - select 3 strategies from the Phase 5 strategy set
  - generate prompt variants
  - score prompt variants
  - select a deterministic recommendation
  - persist session, questions, answers, prompt variants, and scores
- Implemented all Phase 5 prompt strategies in the generator:
  - `diagnostic`
  - `beginner_step_by_step`
  - `expert_consultant`
  - `safety_first`
  - `comparison`
  - `questions_first`
- Added deterministic strategy selection.
  - Risky or `safe_only` inputs include `safety_first`.
  - Inputs with missing required answers include `questions_first`.
  - Comparison intents include `comparison`.
  - Troubleshooting intents include `diagnostic`.
  - Skill level influences beginner versus expert strategy selection.
- Expanded prompt scoring.
  - Scores still use the planned dimensions.
  - Safety-first prompts receive deterministic safety weighting for risky domains.
  - Questions-first prompts receive deterministic weighting when clarification is still needed.
  - Tie-breaking is deterministic by score, strategy priority, and title.

## Verification Notes

- Ran `uv run python -m compileall app` from `apps/api`.
- Ran `uv --directory apps/api run python main.py`.
- Ran a FastAPI `TestClient` Phase 5 pipeline smoke test.
  - High-risk gas/furnace input returned `risk_level = high`.
  - The generated variants included `safety_first`.
  - The recommended prompt was the `safety_first` prompt.
  - All 3 variants had title, strategy, prompt text, score, and explanation.
  - The pipeline returned a `ready` timeline state.
  - A software troubleshooting case with supplied answers completed with `needs_clarification = false`.
  - Both test sessions persisted 3 prompt score rows.
- Verification note:
  - FastAPI emitted a `StarletteDeprecationWarning` from `TestClient` recommending `httpx2`; the endpoint flow still passed.
- Restarted the live API server at `http://127.0.0.1:8000`.
  - Verified `GET /health` returned status `ok` and database status `ok`.
  - Verified live `POST /sessions/{session_id}/run-pipeline` returned 3 prompts.
  - Live high-risk safe-only run recommended `safety_first`.
