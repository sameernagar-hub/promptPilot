# Phase 15.5: Coaching Core and Domain-Aware Platform Gating

## Goal

Apply the pre-Phase-16 update that narrows PromptPilot toward a coaching-first loop and fixes platform-specific prompt scaffolding leaking into non-code domains.

## Status

Complete.

## Execution Progress

- Added domain capability classes for code-like, evidence-heavy, and executable-environment domains.
- Gated Codex/Cursor code scaffolding on code-like domains instead of target platform alone.
- Gated `evidence_first` and `agentic` prompt rendering so creative, craft, and other non-executable requests degrade to lighter source boundaries and guide-style interaction.
- Updated platform scoring metadata, platform summaries, recommended actions, and knowledge retrieval guidance to use the same domain capability logic.
- Added a small coaching habit loop with three explicit habits:
  - missing success criteria
  - missing target audience
  - missing output constraints
- Added persistent `coaching_observations` with evidence excerpts, source session IDs, confidence, applied fixes, and user feedback.
- Added a session feedback endpoint for confirming or rejecting coaching observations.
- Promoted coaching notes in the workspace above the prompt contract, with confirm/reject controls.
- Extended the Phase 14 regression harness to cover:
  - art/craft + Codex avoids code scaffolding
  - software + Codex keeps code scaffolding
  - non-code domains downgrade source strictness and agentic interaction
  - coaching feedback persists and restores
  - success-criteria false-positive guard

## Verification

- `uv --directory apps/api run python -m compileall app`
- `uv --directory apps/api run python ../../evals/promptfoo/phase14_regression.py`
- `pnpm.cmd --dir apps/web lint`
- `pnpm.cmd --dir apps/web build`

## Phase 16 Readiness

Phase 16 can begin after this patch. The remaining deployment constraints are still the same: managed production Postgres, hosted production LLM provider, production CORS origins, and no localhost/Ollama dependency for public traffic.
