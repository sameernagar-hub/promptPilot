# Phase 11: Clarification-First Prompt Refinement

## Goal

Make prompt refinement feel guided instead of jumping straight to a recommended prompt.

In refinement mode, PromptPilot should ask the user critical clarifying questions before generating the final prompt. Users may skip questions, but skipped context should become explicit assumptions.

## Status

Complete.

## Planned Pipeline

```txt
raw request
-> detect and confirm domain
-> inspect profile traits
-> identify missing context
-> ask clarifying questions
-> merge answers and preferences
-> generate detailed prompt
-> explain why this prompt was recommended
```

## Detailed Prompt Contract

```txt
role
task
context
domain
constraints
audience
tone
formality
detail level
temperature or creativity guidance
output format
success criteria
assumptions
follow-up behavior
safety or source boundaries
```

## Planned Work

- [x] Add an explicit refinement mode.
- [x] Generate clarifying questions from domain, profile traits, and missing context.
- [x] Support answer, skip, and revise states.
- [x] Add prompt revision history.
- [x] Add recommendation explanations that reference settings, answers, and profile traits.

## Verification

- [x] Refinement mode asks questions before recommending a prompt.
- [x] Users can answer, skip, or revise clarifying questions.
- [x] Generated prompts include domain, constraints, assumptions, and success criteria.
- [x] Prompt revisions are stored.
- [x] Recommendation explanations identify what shaped the prompt.

## Implementation Notes

- `POST /sessions/{session_id}/run-pipeline` now accepts `mode: "refinement" | "quick"`.
- Refinement mode defers prompt generation while domain confirmation or required clarifying context is still open.
- Clarifying questions store answer state and revision count.
- Skipped or unanswered required context is carried into prompt assumptions and lowers specificity/quality scoring.
- Prompt revisions are stored in `prompt_revisions` with settings, classification, answer/skip IDs, assumptions, and profile trait metadata.
- The workspace exposes a Refine/Quick mode toggle, per-question skip/revise controls, assumptions, explanation text, and revision history.

## Verified Commands

- `uv --directory apps/api run python -m compileall app`
- `pnpm.cmd --dir apps/web lint`
- `pnpm.cmd --dir apps/web build`
- HTTP smoke against `http://127.0.0.1:8000`: first refinement pass returned questions and zero prompts; answered/skipped rerun generated prompts, assumptions, and a stored revision.
