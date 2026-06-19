# Phase 14: Session Onboarding, Live Evaluation, Privacy, and Production Readiness

## Goal

Make PromptPilot trustworthy and useful for real users by adding a session-first onboarding layer, strict guardrails, clean-slate user data, personalized AI-platform guidance, and live evaluation metrics that protect and score the quality of each interactive prompting session.

Core product goal: improve how a person talks to AI.

## Status

Complete.

## Evaluation Posture

- Treat evaluation as a live product pipeline feature, not only a static development benchmark.
- Make `POST /sessions/{session_id}/run-pipeline` the main place where session quality is measured, scored, persisted, and returned to the frontend.
- Evaluate whether PromptPilot improves the user's raw input into a clearer, safer, platform-aware prompt contract.
- Preserve all Phase 0 through Phase 13 behavior, including local Postgres/pgvector schema support, open-domain confirmation, skipped-question assumptions, platform-aware prompt output, and `trait_detector_v1` profile trait signal detection.

## Session and Onboarding Model

- Open the application to a required session-start flow before the main workspace is used.
- Ask for the user's display name.
- Ask which AI system the user primarily wants help with.
- Include common AI platform options: ChatGPT, Claude, Grok, Perplexity, Gemini, Copilot, Cursor, Codex, and Other.
- Treat this as a session profile, not a permanent account, unless a later production auth provider is explicitly added.
- Attach the selected name and AI platform to all session data, profile summaries, prompt refinements, Q&A responses, and saved outputs.
- Provide clear Start New Session and End Session controls.
- Keep the session active across route changes, tab switches, refreshes, and normal app navigation until the user explicitly ends it.
- Ending a session clears local session state and returns the user to onboarding.
- Starting a new session begins from a clean slate and does not inherit example data, imported chats, prompt history, profile observations, or previous scores.
- Require the user to accept a short rules and acceptable-use agreement before the session begins.

## Live Pipeline Evaluation Workflow

```txt
raw user request
-> active session profile and selected target platform
-> open-domain classification and confirmation state
-> clarifying questions, answers, skipped questions, and assumptions
-> platform-aware prompt contract generation
-> dynamic local evaluator scoring through Ollama llama3.1:8b
-> normalized score breakdown, recommendation, explanation, modification rationale, platform-fit breakdown, and recommended actions
-> persisted prompt score records and dashboard-ready API payload
```

## Pipeline Metadata Contract for Phase 15 UX

- Return a modification audit trail that records why the backend altered, expanded, constrained, or reformatted the user's raw request.
- Include skipped-question assumption metadata that maps each skipped required question to the explicit assumption injected into the final prompt.
- Include platform-fit breakdown metadata that can compare selected-platform fit against relevant target architectures such as Codex, Gemini, Claude, ChatGPT/OpenAI, Cursor, and generic assistants.
- Include analytical reasoning metadata in safe, summarized fields such as `rules_matched`, `user_trait_alignment`, `domain_confirmation_influence`, `assumption_sources`, and `optimization_paths`.
- Keep this metadata frontend-ready, compact, and validated so Phase 15 can place it behind progressive disclosure without exposing raw evaluator prompts, chain-of-thought, or internal debug traces.

## Dynamic Session Evaluation Criteria

- `input_to_contract_improvement`: how much the final prompt improves the user's messy raw input into a usable AI instruction.
- `contract_completeness`: whether the prompt contract includes role, task, context, domain, constraints, audience, tone, formality, detail level, output format, success criteria, assumptions, follow-up behavior, and safety/source boundaries.
- `assumption_handling`: whether skipped or unanswered required questions are carried forward as explicit assumptions without pretending the missing context is known.
- `domain_accuracy`: whether detected, confirmed, or corrected domain context is reflected accurately in the prompt and scoring explanation.
- `clarification_value`: whether clarifying questions reduce ambiguity and improve the recommended variant.
- `platform_fit`: whether the prompt is shaped for the selected target platform, including Claude, OpenAI/ChatGPT, Codex, Gemini, Cursor, or generic assistants.
- `platform_fit_granularity`: whether the response can explain the prompt's distinct fit for each relevant target LLM architecture rather than hiding platform behavior in one opaque score.
- `backend_value_exposure`: whether the response makes PromptPilot's improvements visible through concise audit, rules, trait-alignment, and optimization-path metadata.
- `safety_privacy_integrity`: whether sensitive requests, secrets, imported content, and misuse attempts are handled with the correct warnings, redaction, or refusal/redirect behavior.
- `user_actionability`: whether the recommended variant and explanation help the user understand what to do next.

## Ollama-Backed Live Scoring

- Wire the backend evaluation path to local `Ollama` with `llama3.1:8b` for dynamic scoring of generated prompt variants during `POST /sessions/{session_id}/run-pipeline`.
- Use the local model to score prompt quality improvement, contract completeness, assumptions, domain accuracy, and platform fit across the live variants.
- Normalize model output into validated fields before persistence or display, including numeric score dimensions, a recommendation label, a short explanation, and recommended user actions.
- Record the scoring model and scorer version so results can be audited and compared against future scoring changes.
- Keep deterministic rule scoring available as a local fallback only when the evaluator is unavailable, and make that fallback visible in the scorer metadata.

## promptfoo Regression Coverage

- Use `promptfoo` in Phase 14 to test the live scoring algorithms, not as a separate product surface.
- Add a diverse scenario suite under `evals/promptfoo` that calls the live backend workflow or an equivalent scoring harness.
- Cover messy raw prompts, skipped clarifying questions, domain ambiguity and correction, profile-trait influence, target-platform differences, sensitive domains, redaction, and prompt-injection style imported content.
- Assert that scores stay within schema, recommendations rank the strongest variant, skipped questions become assumptions, platform fit changes when the selected platform changes, unsafe requests are not recommended, and explanations remain actionable.
- Run promptfoo before Phase 14 is considered complete so scoring behavior cannot regress silently.

## Evaluation Coverage

```txt
session start and end behavior
session persistence until explicit end
clean-slate session creation
name and AI platform personalization
live run-pipeline scoring behavior
Ollama llama3.1:8b evaluator integration
promptfoo scoring regression suite
input-to-contract improvement
contract completeness
assumption handling for skipped questions
domain accuracy after confirmation or correction
trait detection accuracy
domain detection and confirmation
clarifying question quality
refined prompt completeness
platform-specific prompt fit
recommendation explanation usefulness
profile Q&A grounding
redaction behavior
deletion and reprocessing behavior
guardrail refusal and safe-redirection behavior
```

## Production Features

- Session-scoped profile ownership.
- Optional production authentication only if it improves continuity without weakening clean-slate session behavior.
- Per-session personalization based on display name and selected AI platform.
- Prompt and import history.
- Prompt versioning.
- Feedback and ratings.
- Live evaluation scores and scorer metadata for generated variants.
- Rate limits.
- Model usage and cost tracking.
- Audit logs for model runs and imports.
- Export to Markdown and JSON for sessions and profile data.
- Data reset and deletion flows that work at the session level.

## App Shell and Personalized Experience

- Keep a constant header and footer across the workspace, profile, import, library, and settings routes.
- Make tab and route switching smooth while preserving the active session.
- Make the PromptPilot logo navigate directly to the home workspace.
- Personalize headings, recommendations, profile insights, and prompt guidance with the user's name and selected AI platform.
- Keep the UI minimal and readable.
- Avoid overwhelming users with raw scoring figures; show plain-language guidance first and move detailed metrics into expandable details.
- Route every user-facing generated output through the AI formatting layer so the result is polished for the selected AI platform.
- Do not echo the user's input back as raw labels such as `Problem: ...`; reframe and format outputs according to PromptPilot's product voice.
- Remove seeded examples, demo rows, and precreated profile data from the production session path.

## Security and Safety

- PII handling rules.
- Secret redaction.
- Sensitive-domain warnings.
- Medical, legal, financial, repair, and safety boundaries where appropriate.
- Prompt injection checks for imported or retrieved external content.
- Required rules acceptance before session start.
- Strict misuse guardrails for harmful, deceptive, abusive, or policy-violating requests.
- Safe completion patterns that explain boundaries briefly and redirect to allowed help.
- No persistence of sensitive session data beyond the active session unless the user explicitly chooses an export or future account-based feature.

## Planned Work

- [x] Build the session onboarding screen and session store.
- [x] Add display-name and AI-platform fields to the session model.
- [x] Add the supported AI-platform list with an Other option.
- [x] Add rules acceptance and guardrail checks before entering the workspace.
- [x] Add Start New Session and End Session flows.
- [x] Remove precreated examples and demo data from the default production path.
- [x] Personalize workspace and refinement copy around the active session.
- [x] Extend `POST /sessions/{session_id}/run-pipeline` so live scoring is part of the backend workflow instead of a detached benchmark step.
- [x] Add dynamic scoring dimensions for input-to-contract improvement, contract completeness, assumption handling, domain accuracy, clarification value, platform fit, safety/privacy integrity, and user actionability.
- [x] Add Phase 15-ready metadata fields for modification audit trails, skipped-question assumption sources, platform-fit breakdowns, matched rules, user-trait alignment, and optimization paths.
- [x] Wire local `Ollama` with `llama3.1:8b` into the live scorer for generated prompt variants.
- [x] Normalize and validate deterministic and Ollama-generated score output before it is stored in `prompt_scores`, prompt variant metadata, or API responses.
- [x] Preserve current deterministic scoring behavior as an explicit fallback with visible scorer metadata.
- [x] Add promptfoo scenarios for diverse user requests, skipped questions, domain correction, platform-specific recommendations, sensitive prompts, redaction, and profile-trait influence.
- [x] Use promptfoo assertions to prevent regressions in score schema, ranking, assumptions, domain fit, platform fit, safety behavior, and recommendation explanations.
- [x] Simplify score-heavy UI so user-facing guidance is readable before raw metrics.
- [x] Ensure generated and interpreted outputs use product-facing AI formatting before display.
- [x] Add tests for privacy-critical behaviors.
- [x] Define session, auth, and ownership boundaries before real chat storage.
- [x] Add export and delete flows for session and profile data.
- [x] Add audit logs for model runs, imports, and evaluator/scorer runs.

## Verification

- [x] A new visitor must create a session with name, AI platform, and rules acceptance before using the workspace.
- [x] AI platform options include ChatGPT, Claude, Grok, Perplexity, Gemini, Copilot, Cursor, Codex, and Other.
- [x] Session state persists across route changes and refreshes until End Session is used.
- [x] End Session clears active local session state and returns to onboarding.
- [x] Start New Session creates a clean slate without seeded examples, previous profile observations, imports, or prompt history.
- [x] Header and footer remain stable across tabs and routes.
- [x] Logo click returns to the home workspace.
- [x] User-facing outputs are AI-formatted, personalized, and free of raw `Problem: ...` style echoes.
- [x] Scores are readable and detailed metrics are not the dominant UI.
- [x] `POST /sessions/{session_id}/run-pipeline` returns live evaluation fields for each generated variant.
- [x] Dynamic scores measure prompt quality improvement, contract completeness, assumptions, domain accuracy, and platform fit.
- [x] Skipped clarifying questions are reflected as assumptions and affect scoring confidence or specificity.
- [x] Skipped-question metadata maps each injected assumption back to the missing question or context source.
- [x] Live pipeline responses include modification rationale, rules matched, user-trait alignment, optimization paths, and platform-fit breakdowns for Phase 15 progressive disclosure.
- [x] Confirmed or corrected domains improve domain-fit scoring and explanation text.
- [x] Local `Ollama` with `llama3.1:8b` can score live variants in local development.
- [x] Scorer metadata identifies whether `Ollama` or the deterministic fallback produced the score.
- [x] promptfoo scenarios cover diverse messy user inputs, target platforms, skipped questions, safety/privacy cases, and profile-trait influence.
- [x] promptfoo regression checks pass locally.
- [x] Guardrails block misuse and safely redirect allowed use cases.
- [x] Evaluation suite runs locally.
- [x] Privacy-critical behaviors have tests.
- [x] Session, auth, and ownership boundaries are explicit before storing real user chat history.
- [x] Users can export and delete their session and profile data.
- [x] Audit logs exist for imports, model runs, and scorer runs.
- [x] Existing Phase 0 through Phase 13 behavior remains intact, including local Postgres/pgvector schemas and `trait_detector_v1` signal generation.

## Completion Notes

- `POST /sessions/{session_id}/run-pipeline` now attempts local Ollama scoring with `llama3.1:8b`, accepts multiple model JSON shapes, blends model scores into the deterministic rubric, and records whether `ollama_blended` or deterministic fallback was used.
- Session export/delete and profile export/reset are available through API routes and low-profile UI controls.
- Persistent audit logs now cover session lifecycle, prompt generation, scorer runs, prompt score persistence, model-run previews, guardrail blocks, import create/reprocess/delete, and profile reset.
- The workspace, onboarding, profile, imports, library, and settings routes now share a stable app frame or matching footer/header treatment.
- Regression coverage lives under `evals/promptfoo` and passes locally through `phase14_regression.py`.

Verification commands run:

```powershell
uv --directory apps/api run python -m compileall app
uv --directory apps/api run python ..\..\evals\promptfoo\phase14_regression.py
pnpm.cmd --dir apps/web lint
pnpm.cmd --dir apps/web build
git diff --check
```
