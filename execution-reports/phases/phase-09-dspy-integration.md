# Phase 9: DSPy Integration

## Goal

Make the prompt engine structured and optimizable.

## Status

Not started.

## Prerequisites

- Prompt Engine V1 exists.
- Enough examples or ratings are available to evaluate improvements.
- LLM provider abstraction is stable.

## Planned DSPy Signatures

- `ClassifyProblem`
- `GenerateClarifyingQuestions`
- `GeneratePromptVariants`
- `ScorePromptVariant`

## Planned Inputs and Outputs

### ClassifyProblem

- Input: `problem`
- Output: `domain`, `intent`, `risk_level`

### GenerateClarifyingQuestions

- Input: `problem`, `domain`, `intent`
- Output: `questions`

### GeneratePromptVariants

- Input: `problem`, `domain`, `settings`, `retrieved_patterns`
- Output: `variants`

### ScorePromptVariant

- Input: `problem`, `prompt_text`, `settings`
- Output: `score`, `explanation`

## Verification

- [ ] DSPy module can replace or wrap rule-based services.
- [ ] Outputs conform to existing schemas.
- [ ] Optimizers are only introduced after examples and ratings exist.
