# Phase 15: Codebase Cleanup, AI-Formatted Outputs, Knowledge Support, and Pre-Deploy Polish

## Goal

Prepare PromptPilot for Phase 16 Vercel deployment by cleaning the codebase, simplifying the product surface, documenting the architecture, and ensuring AI-generated scoring explanations, platform-fit ratings, backend modification rationale, and recommended actions are cleanly formatted for minimalist Next.js dashboards.

## Status

In progress.

## Execution Progress

- Single-port cleanup is complete: local web uses port `3000`, local API uses port `8000`, and default docs/config no longer use an extra preview smoke port.
- Dashboard scoring-output polish is complete for the main workspace:
  - default prompt header shows platform-readiness text instead of a raw numeric score
  - backend explanations are product-facing and session-aware
  - recommended micro-actions render as a compact optimization HUD
  - score breakdowns, platform-fit details, modification audit trails, assumptions, rules matched, trait alignment, optimization paths, and scorer status stay behind expandable evaluation details
- Production environment hardening has started:
  - API runtime rejects production startup when `DATABASE_URL`, `LLM_PROVIDER`, or `ALLOWED_ORIGINS` still point at local-only services
  - frontend API calls require `NEXT_PUBLIC_API_BASE_URL` outside local development

## Codebase Cleanup

- Remove or archive unnecessary local-only artifacts before deployment, including stale screenshots, temporary smoke-test output, outdated status notes, unused changelog drafts, and obsolete planning fragments.
- Keep the useful execution reports, but make the current status and roadmap concise enough to support deployment.
- Audit `.gitignore`, environment examples, generated files, local logs, and development-only assets.
- Remove seeded demo data paths from production startup.
- Make sure no production code depends on local-only services such as `localhost`, local Docker, or local Ollama, while preserving local Ollama as a documented development evaluator from Phase 14.
- Ensure the app can run from a clean install using documented commands and environment variables.
- Keep the implementation minimal by removing unused components, dead API routes, orphaned helpers, stale constants, and old UI copy.

## Local Port and Deployment Simplification

- Keep exactly one local frontend port and one local API port for the full project:
  - Frontend: `http://localhost:3000` or `http://127.0.0.1:3000`.
  - API: `http://localhost:8000` or `http://127.0.0.1:8000`.
- Remove extra preview smoke ports from local docs, environment examples, default CORS origins, and startup scripts.
- Use the same frontend port for dev and local production-build smoke checks; stop the dev server before running `next start`.
- Keep Vercel deployment docs production-first: deploy final API and final web projects with production environment variables, not a separate preview-port workflow.
- CORS should allow only the single local frontend port during development plus the final production web origin during deployment.

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

## Maximum Value and Minimalist UX Requirements

### Explicit Backend Value Exposure

- Add a modification audit trail requirement for the post-execution UI: every backend alteration to the user's raw request must have a concise, inspectable explanation of why it happened.
- When a user skips a clarifying question, the UI must explicitly flag the corresponding injected assumption, such as showing that an assumption was added because required context was missing.
- Surface platform-fit granularity instead of a single generic score: the UI must explain how the final prompt strategy optimizes differently for target LLM architectures such as Codex, Gemini, Claude, ChatGPT/OpenAI, Cursor, and generic assistants.
- Require platform-fit details to show distinct ratings or behaviors where relevant, such as Codex emphasizing repository context and verification, Gemini supporting broad or multimodal context, and Claude favoring long-context structure and nuance.
- Expose analytical reasoning metadata from the pipeline in a user-safe form, including matched rules, user-trait alignment, skipped-question assumptions, confirmed or corrected domain influence, and specific optimization paths taken.
- Keep all metadata explanatory and product-facing; never surface raw chain-of-thought, evaluator prompts, unvalidated model chatter, or internal debug traces.

### Progressive Disclosure Guardrails

- Preserve a zero-clutter default: the first post-execution state must keep visual focus on the primary recommended prompt output.
- Move scoring explanations, modification logs, platform metrics, rule matches, trait-alignment details, and recommended next steps behind progressive disclosure controls such as hoverable tooltips, collapsible accordions, drawers, or compact tabs.
- Provide an actionable optimization HUD as a low-profile recommendation area, not a wall of text.
- Express high-leverage next steps as concrete micro-actions, such as `[+] Add Source Constraints` or `[+] Add Audience Detail`, with expected impact when available, such as improving platform fit or reducing assumption risk.
- Keep the HUD secondary to the generated prompt and avoid generic recommendation blocks that compete with the main output.

## AI-Formatted Scoring Output

- Ensure AI-generated scoring explanations, platform-fit ratings, and recommended actions are cleanly formatted and safe to surface in the Next.js workspace, comparison view, profile dashboard, and future evaluation dashboards.
- Define a frontend-ready scoring contract that can include `score_total`, `score_breakdown`, `platform_fit_rating`, `platform_fit_breakdown`, `recommendation_label`, `recommendation_summary`, `why_this_variant`, `assumption_notes`, `modification_audit_trail`, `rules_matched`, `user_trait_alignment`, `optimization_paths`, `recommended_actions`, and `scorer_metadata`.
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
- [x] Local development uses only one frontend port, `3000`, and one API port, `8000`; no extra preview ports remain in default config or docs.
- [x] Production runtime fails fast if Vercel/API environment values would point to localhost, local Docker, or local Ollama.
- [x] `README.md`, `apps/api/README.md`, and `apps/web/README.md` accurately explain architecture, setup, functionality, sessions, guardrails, live evaluation, scorer metadata, dashboard output, and deployment.
- [x] Current status, changelog, and phase docs do not conflict with the Phase 16 Vercel deployment plan.
- [ ] The app remains minimal, responsive, and readable on mobile, tablet, and desktop.
- [x] The first post-execution view is zero-clutter and keeps primary focus on the recommended prompt output.
- [ ] Session state sticks until the user explicitly ends it.
- [ ] No seeded demo examples or precreated user data appear in a new production session.
- [x] All user-facing interpreted outputs are AI-formatted and personalized.
- [x] Scoring explanations, platform-fit ratings, modification audit trails, platform-fit breakdowns, and recommended actions are formatted for frontend display.
- [x] Skipped clarifying questions visibly map to injected assumptions in the advanced details UI.
- [x] Rules matched, user-trait alignment, and optimization paths are available behind progressive disclosure without exposing raw internals.
- [x] The optimization HUD presents concrete micro-actions instead of generic explanatory text blocks.
- [x] Recommended variants explain why they fit the selected target platform, including Claude versus OpenAI/ChatGPT-style differences when relevant.
- [x] Dashboard copy translates scores into actionable user feedback instead of exposing raw evaluator internals.
- [ ] Output guardrails prevent raw JSON, chain-of-thought, unvalidated evaluator text, raw `Problem: ...` echoes, and confusing score dumps from appearing in the UI.
- [ ] Knowledge sources are licensed and tracked.
- [ ] RAG outputs are synthesized rather than copied.
- [ ] DSPy modules conform to existing schemas.
- [ ] Agent tracks improve guided workflows without hiding user control.
- [ ] Retrieved content cannot override user settings, confirmed domain, safety rules, scorer output contract, or profile preferences.
- [ ] Local lint, build, API compile, and smoke checks pass immediately before Phase 16 begins.
