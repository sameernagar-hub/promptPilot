# Phase 15: Knowledge Base, RAG, DSPy, and Agent Tracks

## Goal

Bring back the old knowledge base, retrieval, DSPy, and agent-track ideas as support systems for the user-profile product.

## Status

Not started.

## Prompt Knowledge Base Role

- Store licensed prompt patterns and project-created examples.
- Track source, URL, author, license, allowed usage, domain, intent, prompt type, and quality score.
- Prefer pattern extraction and synthesis over copying.

## RAG Role

- Retrieve useful prompt structures and domain patterns.
- Keep retrieved context subordinate to user settings, confirmed domain, safety rules, and profile preferences.
- Preserve license metadata.

## DSPy Role

- Structure classification, clarification, refinement, scoring, and profile Q&A modules.
- Use optimizers only after enough examples, feedback, and evaluation cases exist.

## Agent Tracks Role

- Convert repeated workflows into guided tracks after the profile and refinement system is stable.
- Initial tracks can include Fix Something, Build Something, Learn Something, Write Something, Compare Options, and Research Topic.

## Verification

- [ ] Knowledge sources are licensed and tracked.
- [ ] RAG outputs are synthesized rather than copied.
- [ ] DSPy modules conform to existing schemas.
- [ ] Agent tracks improve guided workflows without hiding user control.
- [ ] Retrieved content cannot override user settings, confirmed domain, safety rules, or profile preferences.
