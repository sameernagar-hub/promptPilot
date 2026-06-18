# Phase 14: Session Onboarding, Evaluation, Privacy, and Production Readiness

## Goal

Make PromptPilot trustworthy and usable for real users by adding a session-first onboarding layer, strict guardrails, clean-slate user data, personalized AI-platform guidance, and evaluation coverage for privacy-critical behavior.

## Status

Not started.

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

## Evaluation Coverage

```txt
session start and end behavior
session persistence until explicit end
clean-slate session creation
name and AI platform personalization
trait detection accuracy
domain detection and confirmation
clarifying question quality
refined prompt completeness
platform-specific prompt fit
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
- Rate limits.
- Model usage and cost tracking.
- Audit logs for model runs and imports.
- Export to Markdown, PDF, and JSON.
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

- Build the session onboarding screen and session store.
- Add display-name and AI-platform fields to the session model.
- Add the supported AI-platform list with an Other option.
- Add rules acceptance and guardrail checks before entering the workspace.
- Add Start New Session and End Session flows.
- Remove precreated examples and demo data from the default production path.
- Personalize workspace, profile, refinement, and Q&A copy around the active session.
- Simplify score-heavy UI so user-facing guidance is readable before raw metrics.
- Ensure all generated outputs pass through the AI formatter before display.
- Add or extend the evaluation suite.
- Add tests for privacy-critical behaviors.
- Define session, auth, and ownership boundaries before real chat storage.
- Add export and delete flows for profile data.
- Add audit logs for model runs and imports.

## Verification

- [ ] A new visitor must create a session with name, AI platform, and rules acceptance before using the workspace.
- [ ] AI platform options include ChatGPT, Claude, Grok, Perplexity, Gemini, Copilot, Cursor, Codex, and Other.
- [ ] Session state persists across route changes and refreshes until End Session is used.
- [ ] End Session clears active local session state and returns to onboarding.
- [ ] Start New Session creates a clean slate without seeded examples, previous profile observations, imports, or prompt history.
- [ ] Header and footer remain stable across tabs and routes.
- [ ] Logo click returns to the home workspace.
- [ ] User-facing outputs are AI-formatted, personalized, and free of raw `Problem: ...` style echoes.
- [ ] Scores are readable and detailed metrics are not the dominant UI.
- [ ] Guardrails block misuse and safely redirect allowed use cases.
- [ ] Evaluation suite runs locally.
- [ ] Privacy-critical behaviors have tests.
- [ ] Session, auth, and ownership boundaries are explicit before storing real user chat history.
- [ ] Users can export and delete their profile data.
- [ ] Audit logs exist for imports and model runs.
