# Phase 12: Advanced Controls and Target Platform Output

## Goal

Let users shape prompts for the AI system they plan to use.

This phase expands the current tuner into platform-aware controls while keeping the UI usable.

## Status

Not started.

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

- Extend backend prompt settings schemas.
- Extend frontend tuner controls.
- Persist platform preferences with sessions and profiles.
- Add platform-specific prompt generation templates.
- Add platform-fit scoring.
- Add settings defaults from the user profile when available.

## Verification

- [ ] Settings persist with sessions.
- [ ] Platform preferences persist with the profile.
- [ ] Prompt output changes based on selected platform.
- [ ] UI exposes advanced controls without becoming cluttered.
- [ ] Prompt scoring accounts for platform fit.
