# Prompt Intelligence Engine

The active engine studies imported prompts and produces a prompt intelligence report. It is not a first-screen prompt generator.

## Active Pipeline

1. Accept an import request from pasted text, Markdown, JSON, or an existing import id.
2. Normalize the content into conversations and messages.
3. Redact obvious secrets before previews.
4. Refresh the local prompt intelligence profile from user-authored messages.
5. Build evidence excerpts from imported user prompts.
6. Use OpenAI Responses API when configured to analyze prompting behavior.
7. Fall back to deterministic local analysis when OpenAI is unavailable.
8. Store a report with headline, summary, style scores, behavior patterns, recommendations, next-prompt recipe, comparisons, evidence, provider, model, and metadata.
9. Render the latest report in the web app.

## Scoring Dimensions

Prompt intelligence reports score:

- Goal clarity
- Context depth
- Constraint specificity
- Evidence discipline
- Iteration signal
- Platform specificity

Scores are behavior signals, not a moral grade and not a template-compliance score.

## Legacy Engine

The older session prompt engine, variant generation, scorer, saved prompts, knowledge retrieval, and DSPy adapters remain in the backend for historical data, regression coverage, and future reuse. They are not the active product surface for Phase 16.
