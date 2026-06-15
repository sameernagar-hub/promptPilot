# Phase 5: Prompt Engine V1

## Goal

Build the first working prompt generation pipeline.

## Status

Not started.

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

- [ ] Pipeline can run without an external LLM.
- [ ] Each variant has title, strategy, prompt text, score, and explanation.
- [ ] Safety-first logic appears for risky domains.
- [ ] Recommended variant is selected deterministically.
