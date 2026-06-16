# Phase 11: Clarification-First Prompt Refinement

## Goal

Make prompt refinement feel guided instead of jumping straight to a recommended prompt.

In refinement mode, PromptPilot should ask the user critical clarifying questions before generating the final prompt. Users may skip questions, but skipped context should become explicit assumptions.

## Status

Not started.

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

- Add an explicit refinement mode.
- Generate clarifying questions from domain, profile traits, and missing context.
- Support answer, skip, and revise states.
- Add prompt revision history.
- Add recommendation explanations that reference settings, answers, and profile traits.

## Verification

- [ ] Refinement mode asks questions before recommending a prompt.
- [ ] Users can answer, skip, or revise clarifying questions.
- [ ] Generated prompts include domain, constraints, assumptions, and success criteria.
- [ ] Prompt revisions are stored.
- [ ] Recommendation explanations identify what shaped the prompt.
