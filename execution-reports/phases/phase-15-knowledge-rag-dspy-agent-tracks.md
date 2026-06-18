# Phase 15: Codebase Cleanup, AI-Formatted Outputs, Knowledge Support, and Pre-Deploy Polish

## Goal

Prepare PromptPilot for Phase 16 Vercel deployment by cleaning the codebase, simplifying the product surface, documenting the architecture, and ensuring AI-generated scoring explanations, platform-fit ratings, and recommended actions are cleanly formatted for the Next.js dashboards.

## Status

Not started.

## Codebase Cleanup

- Remove or archive unnecessary local-only artifacts before deployment, including stale screenshots, temporary smoke-test output, outdated status notes, unused changelog drafts, and obsolete planning fragments.
- Keep the useful execution reports, but make the current status and roadmap concise enough to support deployment.
- Audit `.gitignore`, environment examples, generated files, local logs, and development-only assets.
- Remove seeded demo data paths from production startup.
- Make sure no production code depends on local-only services such as `localhost`, local Docker, or local Ollama, while preserving local Ollama as a documented development evaluator from Phase 14.
- Ensure the app can run from a clean install using documented commands and environment variables.
- Keep the implementation minimal by removing unused components, dead API routes, orphaned helpers, stale constants, and old UI copy.

## README and Documentation Cleanup

- Rewrite the root `README.md` so it explains the final architecture, setup, environment variables, local development, API usage, frontend routes, session model, guardrails, profile behavior, live evaluation behavior, exports, and deployment path.
- Update `apps/api/README.md` with API architecture, endpoints, persistence, session data flow, safety checks, live scoring flow, scorer metadata, and production environment variables.
- Update `apps/web/README.md` with app shell structure, routes, session onboarding, dashboard scoring display, responsive design, and build/deploy commands.
- Update execution reports so the current phase status is accurate and no stale "current status" text conflicts with the Phase 16 deployment plan.
- Document how to start, end, and reset a session.
- Document what data persists only for the active session and what can be exported.

## Minimal UX and Session Continuity

- Make the app visually minimal, responsive, and focused on the active session.
- Keep header and footer constant across route changes.
- Keep the logo linked to the home workspace.
- Preserve the active session until the user explicitly ends it.
- Keep all major flows accessible from the main workspace without requiring users to understand internal scores or model plumbing.
- Prefer plain-language guidance over dense dashboards.
- Hide raw scoring figures, traces, and implementation details behind optional expanded views.
- Keep mobile, tablet, and desktop layouts polished before deployment.

## AI-Formatted Scoring Output

- Ensure AI-generated scoring explanations, platform-fit ratings, and recommended actions are cleanly formatted and safe to surface in the Next.js workspace, comparison view, profile dashboard, and future evaluation dashboards.
- Define a frontend-ready scoring contract that can include `score_total`, `score_breakdown`, `platform_fit_rating`, `recommendation_label`, `recommendation_summary`, `why_this_variant`, `assumption_notes`, `recommended_actions`, and `scorer_metadata`.
- Keep score explanations short, specific, and user-facing. They should explain why a variant is recommended for the selected platform, such as Claude versus OpenAI/ChatGPT, without exposing raw evaluator prompts or model chatter.
- Translate evaluation metrics into clear feedback about how the user's raw request improved, what assumptions remain, which domain details matter, and what action the user should take next.
- Make platform-fit guidance explicit: explain why a Claude prompt may emphasize long-context structure and nuance, why an OpenAI/ChatGPT prompt may emphasize portable explicit instructions, why a Codex prompt may emphasize repository context and verification, and why generic prompts avoid provider-specific assumptions.
- Guardrail output formatting so dashboard text never appears as raw JSON, chain-of-thought, internal scoring rubrics, unvalidated model output, or raw `Problem: ...` echoes.
- Put detailed numeric metrics behind expandable UI while leading with the recommendation, plain-language rationale, and next action.

## AI-First Output Polish

- Ensure every visible output that interprets or rewrites user intent goes through the AI formatting layer.
- Personalize output using the active session name and selected AI platform.
- Keep generated responses aligned with the selected AI platform's expected style.
- Remove raw echo formats such as `Problem: ...` unless they are part of a deliberate export format.
- Ensure the product voice stays consistent across workspace, profile, imports, library, exports, and Q&A.
- Include scoring explanations and recommended actions in the same formatting pass so evaluation output feels like product guidance, not a developer report.

## Prompt Knowledge Base Role

- Store licensed prompt patterns and project-created examples only when they support personalized refinement without seeding visible demo data into new sessions.
- Track source, URL, author, license, allowed usage, domain, intent, prompt type, and quality score.
- Prefer pattern extraction and synthesis over copying.

## RAG Role

- Retrieve useful prompt structures and domain patterns.
- Keep retrieved context subordinate to user settings, confirmed domain, safety rules, profile preferences, and live evaluation guardrails.
- Preserve license metadata.
- Ensure retrieved content cannot override the active session profile, rules acceptance, selected AI platform, scorer output contract, or guardrails.

## DSPy Role

- Structure classification, clarification, refinement, scoring, and profile Q&A modules.
- Use optimizers only after enough examples, feedback, and evaluation cases exist.
- Keep DSPy modules behind stable schemas so the UI receives polished guidance instead of raw intermediate scores.

## Agent Tracks Role

- Convert repeated workflows into guided tracks after the profile and refinement system is stable.
- Initial tracks can include Fix Something, Build Something, Learn Something, Write Something, Compare Options, and Research Topic.
- Keep agent tracks optional and session-aware, with the same guardrails and AI-formatting rules as the main workspace.

## Verification

- [ ] Codebase cleanup removes stale local-only artifacts, unused files, obsolete UI copy, and production-blocking assumptions.
- [ ] `README.md`, `apps/api/README.md`, and `apps/web/README.md` accurately explain architecture, setup, functionality, sessions, guardrails, live evaluation, scorer metadata, dashboard output, and deployment.
- [ ] Current status, changelog, and phase docs do not conflict with the Phase 16 Vercel deployment plan.
- [ ] The app remains minimal, responsive, and readable on mobile, tablet, and desktop.
- [ ] Session state sticks until the user explicitly ends it.
- [ ] No seeded demo examples or precreated user data appear in a new production session.
- [ ] All user-facing interpreted outputs are AI-formatted and personalized.
- [ ] Scoring explanations, platform-fit ratings, and recommended actions are formatted for frontend display.
- [ ] Recommended variants explain why they fit the selected target platform, including Claude versus OpenAI/ChatGPT-style differences when relevant.
- [ ] Dashboard copy translates scores into actionable user feedback instead of exposing raw evaluator internals.
- [ ] Output guardrails prevent raw JSON, chain-of-thought, unvalidated evaluator text, raw `Problem: ...` echoes, and confusing score dumps from appearing in the UI.
- [ ] Knowledge sources are licensed and tracked.
- [ ] RAG outputs are synthesized rather than copied.
- [ ] DSPy modules conform to existing schemas.
- [ ] Agent tracks improve guided workflows without hiding user control.
- [ ] Retrieved content cannot override user settings, confirmed domain, safety rules, scorer output contract, or profile preferences.
- [ ] Local lint, build, API compile, and smoke checks pass immediately before Phase 16 begins.
