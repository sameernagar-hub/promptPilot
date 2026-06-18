# Phase 12: Advanced Controls and Target Platform Output

## Goal

Let users shape prompts for the AI system they plan to use.

This phase expands the current tuner into platform-aware controls while keeping the UI usable.

## Status

Complete.

## New Controls

```txt
target_platform: codex | claude | chatgpt | gemini | cursor | generic
detail_level: concise | balanced | exhaustive
formality: casual | neutral | formal
temperature: precise | balanced | creative
reasoning_style: direct_answer | step_by_step | ask_first | explore_options
source_strictness: none | cite_when_needed | official_only | evidence_first
interaction_mode: one_shot | iterative | agentic
```

## Platform Behavior

- Codex prompts should emphasize repo context, constraints, files, verification, and expected code-change behavior.
- Claude prompts should support long-context analysis, nuanced reasoning, and careful structure.
- ChatGPT prompts should be general-purpose, explicit, and portable.
- Gemini prompts should support multimodal or broad research use cases when relevant.
- Generic prompts should avoid provider-specific assumptions.

## Planned Work

- [x] Extend backend prompt settings schemas.
- [x] Extend frontend tuner controls.
- [x] Persist platform preferences with sessions and profiles.
- [x] Add platform-specific prompt generation templates.
- [x] Add platform-fit scoring.
- [x] Add settings defaults from the user profile when available.

## Implementation Notes

- `PromptSettings` now includes target platform, detail level, formality, temperature preference, reasoning style, source strictness, and interaction mode.
- `run-pipeline` stores platform preferences in the active local prompting profile so future workspace sessions can inherit the latest valid preferences.
- Prompt generation now emits platform-shaped recommended prompts for Codex, Claude, ChatGPT, Gemini, Cursor, and generic assistants.
- Prompt scoring now includes `platform_fit` and recommendation explanations mention the selected platform and detail level.
- The workspace preferences panel is grouped into Platform, Output, and Legacy Fit sections to keep the expanded controls scannable.
- The workspace loads saved platform preferences from `GET /profile` for a fresh local session.

## Verification

- [x] Settings persist with sessions.
- [x] Platform preferences persist with the profile.
- [x] Prompt output changes based on selected platform.
- [x] UI exposes advanced controls without becoming cluttered.
- [x] Prompt scoring accounts for platform fit.

Verified commands and checks:

- `uv --directory apps/api run python -m compileall app`
- `pnpm.cmd --dir apps/web lint`
- `pnpm.cmd --dir apps/web build`
- HTTP smoke against the running API/Postgres verified Codex-specific prompt text, stored platform preference, `platform_fit`, and platform-aware explanation text.
- HTTP comparison smoke verified Codex and ChatGPT prompts produce different platform behavior.
- In-app Browser was unavailable; headless Chrome fallback verified the workspace preferences panel and saved profile defaults.
