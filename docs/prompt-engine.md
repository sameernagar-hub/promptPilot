# Prompt Engine

The first prompt engine uses rule-based logic for the completed MVP. The Phase 15 engine keeps that stable path while adding guarded knowledge retrieval and schema-stable DSPy adapter modules for future optimization.

Current MVP stages:

1. Classify the raw problem.
2. Generate clarifying questions.
3. Merge answers and tuning settings.
4. Apply optional agent-track metadata as a workflow hint.
5. Retrieve licensed prompt-pattern guidance when matching knowledge sources exist.
6. Produce multiple prompt variants.
7. Score and recommend the best option.

Next refinement stages:

1. Detect the domain and ask the user to confirm or correct it.
2. Inspect the user's prompting profile for relevant traits.
3. Ask clarifying questions before recommending a refined prompt.
4. Merge answers, profile preferences, tuner settings, and any licensed retrieved pattern guidance.
5. Generate a detailed platform-aware prompt.
6. Explain which domain signals, answers, settings, profile traits, assumptions, and safe retrieval patterns shaped the recommendation.

Knowledge and retrieval rules:

- Knowledge sources must include license and allowed-usage metadata before retrieval can use them.
- Retrieval returns synthesized structural guidance, not copied source prompt text.
- Retrieved guidance cannot override the active request, confirmed domain, user settings, safety rules, scorer output contract, or profile preferences.
- With an empty knowledge base, the prompt engine behaves as before and records that no licensed patterns were retrieved.

DSPy support:

- DSPy modules wrap classification, clarification, refinement, and scoring behind existing Pydantic schemas.
- Optimizer traces, intermediate scores, and raw model chatter stay out of UI-facing responses.
- Optimizers should be introduced only after enough examples, feedback, and evaluation cases exist.

Agent-track support:

- Tracks cover Fix, Build, Learn, Write, Compare, and Research workflows.
- A selected track can tune ordinary prompt settings and appears in session metadata as `agent_track`.
- Track metadata is a workflow hint only and cannot override the user's request, settings, confirmed domain, safety rules, or profile preferences.
