# PromptPilot Execution Log

Project name: PromptPilot
Project purpose: Build a full-stack prompting experience platform that understands how a user prompts, builds a useful prompting profile, asks clarifying questions, and generates detailed prompts shaped for the user's domain, preferences, and target AI platform.

Created by: Codex
Initial project folder: Downloads/promptPilot

---

## Product Definition

PromptPilot is not a static prompt template library. It is a prompting intelligence and refinement layer.

Core idea:

1. User describes a problem in natural language.
2. The system detects the domain, intent, risk, and likely user need, then asks the user to confirm or correct the domain.
3. The system asks clarifying questions before recommending a refined prompt.
4. The user tunes prompt style, depth, tone, formality, temperature, risk posture, source strictness, and output format.
5. The engine generates detailed prompt variants for the chosen domain and target AI platform.
6. The variants are scored, compared, and recommended with reasons.
7. The user can copy, save, revise, improve, or run the prompt through an AI model.
8. The system can import or connect previous AI chats, detect prompting traits, and build a profile of the user's prompting patterns.
9. Later phases expand this into Codex, Claude, ChatGPT, Gemini, MCP, and other platform integrations.

Primary promise:

Understand how you prompt. Then help you ask every AI system better.

---

## Original MVP

The MVP is complete when a user can:

1. Enter a messy problem.
2. Get automatic domain and intent detection.
3. Answer clarifying questions.
4. Tune prompt settings.
5. Generate at least 3 prompt variants.
6. Compare prompt scores and explanations.
7. Copy or run the selected prompt.
8. Save prompts to a personal library.

Initial MVP domains:

1. Car/home troubleshooting
2. Software/project building
3. Writing/business communication
4. Learning/research

The revised roadmap keeps this MVP as the completed foundation, but future phases should not be limited to these starter domains. The next direction is open domain detection, domain confirmation, user prompting profiles, chat history import, and platform-aware refinement.

---

## Recommended Stack

Frontend:

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- lucide-react

Backend:

- FastAPI
- Python 3.10+
- Pydantic
- SQLAlchemy
- Uvicorn

Database:

- Postgres
- pgvector for prompt embeddings and semantic search

LLM and AI tooling:

- LiteLLM for model gateway and provider abstraction
- Ollama for local/free model support
- DSPy for structured prompt generation and prompt optimization
- promptfoo for prompt testing and evaluation
- Langfuse for tracing, prompt management, versioning, evaluation, and observability

Future workflow/agent layer:

- CrewAI or AutoGen for multi-agent flows
- MCP for tool integrations
- Langflow, Dify, or Flowise for optional visual workflow building

---

## Folder Structure To Create

Use this structure for the full project:

```txt
promptPilot/
  apps/
    web/
    api/
  packages/
    shared/
  infra/
    docker-compose.yml
  docs/
    architecture.md
    product-spec.md
    prompt-engine.md
  scripts/
  datasets/
    prompt-sources/
  evals/
    promptfoo/
  .env.example
  README.md
  EXECUTION_LOG.md
```

---

## Phase 0: Local Environment Setup

Goal: Prepare local development tools.

Required checks:

```bash
node --version
pnpm --version
python --version
uv --version
docker --version
ollama --version
```

Install if missing:

```bash
npm install -g pnpm
pip install uv
```

Install external applications:

- Docker Desktop
- Ollama from https://ollama.com/

Pull an initial local model:

```bash
ollama pull llama3.1:8b
```

Notes:

- Use Ollama for local development to reduce API cost.
- Use LiteLLM so the app can switch between Ollama, OpenAI, Anthropic, Gemini, and other providers later.

---

## Phase 1: Create Monorepo Boilerplate

Goal: Initialize a full-stack project structure.

Commands:

```bash
mkdir -p apps packages infra docs scripts datasets/prompt-sources evals/promptfoo
```

Create frontend:

```bash
pnpm create next-app apps/web --typescript --tailwind --eslint
cd apps/web
pnpm add lucide-react class-variance-authority clsx tailwind-merge
pnpm dlx shadcn@latest init
```

Create backend:

```bash
cd apps/api
uv init
uv add fastapi uvicorn pydantic sqlalchemy psycopg[binary] pgvector python-dotenv litellm dspy-ai
```

Create root files:

```txt
README.md
.env.example
.gitignore
```

---

## Phase 2: Infrastructure

Goal: Add database and local services.

Create `infra/docker-compose.yml` with Postgres and pgvector:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: prompt_engine
      POSTGRES_USER: prompt_engine
      POSTGRES_PASSWORD: prompt_engine
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Create `apps/api/.env.example`:

```txt
DATABASE_URL=postgresql://prompt_engine:prompt_engine@localhost:5432/prompt_engine
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=ollama/llama3.1:8b
```

Optional later services:

- Langfuse
- LiteLLM proxy
- Qdrant or Chroma if pgvector is not enough

---

## Phase 3: Backend API Skeleton

Goal: Build the first FastAPI service.

Create these backend modules:

```txt
apps/api/
  app/
    main.py
    config.py
    db.py
    models.py
    schemas.py
    services/
      classifier.py
      question_generator.py
      prompt_generator.py
      prompt_scorer.py
      llm_client.py
    routers/
      sessions.py
      prompts.py
      health.py
```

Initial endpoints:

```txt
GET  /health
POST /sessions
GET  /sessions/{session_id}
POST /sessions/{session_id}/classify
POST /sessions/{session_id}/questions
POST /sessions/{session_id}/answers
POST /sessions/{session_id}/generate-prompts
POST /sessions/{session_id}/score-prompts
POST /sessions/{session_id}/run-prompt
POST /prompts/{prompt_id}/save
GET  /saved-prompts
```

Start with simple rule-based logic, then replace with DSPy and retrieval later.

---

## Phase 4: Database Models

Goal: Store sessions, prompts, scores, and future prompt sources.

Core tables:

```txt
users
problem_sessions
clarifying_questions
prompt_variants
prompt_scores
saved_prompts
prompt_sources
prompt_embeddings
domain_packs
```

Important fields:

ProblemSession:

```txt
id
raw_input
detected_domain
detected_intent
risk_level
user_settings
status
created_at
updated_at
```

PromptVariant:

```txt
id
session_id
title
strategy
prompt_text
recommendation_label
score_total
score_breakdown
explanation
created_at
```

PromptSource:

```txt
id
source_name
source_url
license
raw_text
normalized_text
domain
intent
format
risk_level
embedding
created_at
```

---

## Phase 5: Prompt Engine V1

Goal: Build the first working prompt generation pipeline.

Pipeline:

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

Prompt strategies:

```txt
diagnostic
beginner_step_by_step
expert_consultant
safety_first
comparison
questions_first
```

Prompt tuning settings:

```txt
length: short | medium | deep
skill_level: beginner | practical | expert
tone: direct | friendly | technical
format: checklist | guide | table | conversation | plan
risk: safe_only | normal | advanced
sources: none | web | official_docs
```

Scoring dimensions:

```txt
clarity
specificity
safety
actionability
domain_fit
beginner_friendliness
expected_answer_quality
```

---

## Phase 6: Frontend MVP

Goal: Build a usable app as the first screen, not a landing page.

Screens:

```txt
/                Main workspace
/sessions/[id]   Session detail
/compare/[id]    Prompt comparison view
/library         Saved prompt library
/settings        Model and user settings
```

Main workspace layout:

```txt
Left: problem input and clarifying question form
Center: prompt variant cards
Right: tuner panel
Bottom or side: generation timeline
```

UI components:

```txt
ProblemInput
DomainBadge
ClarifyingQuestions
PromptTuner
PromptCard
PromptScoreBars
PromptCompareGrid
AgentTimeline
RunPromptPanel
SavedPromptList
ModelSelector
```

Use lucide-react icons for buttons:

```txt
Copy
Play
Save
RefreshCw
SlidersHorizontal
GitCompare
Sparkles
ShieldCheck
```

Design direction:

- Clean workspace UI
- Dark/light support optional
- Prompt cards with score bars
- Side-by-side compare mode
- Tuner controls with sliders, segmented controls, toggles, and select menus
- Timeline showing Classified -> Questions -> Generated -> Scored -> Ready

---

## Phase 7: Prompting Profile Foundation

Goal: Pivot the product from prompt generation to prompting experience intelligence.

This phase replaces the old prompt knowledge base as the next step. The foundation should let PromptPilot store what a user tends to do when prompting, what the system observed, what evidence supports each observation, and how those traits should influence future prompt refinement.

Core data model additions:

```txt
user_prompt_profiles
prompting_traits
trait_observations
conversation_imports
imported_conversations
imported_messages
prompt_revisions
domain_confirmations
platform_preferences
integration_connections
```

Trait taxonomy seed:

```txt
context_depth
goal_clarity
constraint_specificity
domain_precision
format_preference
tone_preference
formality_preference
iteration_style
risk_awareness
source_expectation
technical_depth
missing_context_patterns
```

Required UX:

- Add a Profile area to the app shell.
- Add a first version of the profile summary, even if it is based only on local sessions.
- Show observed traits with confidence and short supporting examples.
- Store profile data separately from generated prompt variants.

Verification:

- Profile tables or equivalent schema exist.
- Existing sessions can be summarized into profile observations.
- Profile observations include confidence and evidence references.
- The app can show an empty, partial, and populated prompting profile state.

---

## Phase 8: Prompting Trait Detection

Goal: Analyze sessions and imported chats to recognize how the user prompts.

Trait detection should identify patterns rather than judge the user. The output should be practical, explainable, and useful for future prompt refinement.

Detection pipeline:

```txt
collect prompt/session/chat examples
-> normalize examples
-> extract behavioral signals
-> map signals to prompting traits
-> calculate confidence
-> store evidence snippets
-> update the user prompting profile
```

Initial traits to detect:

- Whether prompts usually include enough context.
- Whether the user states a clear outcome.
- Whether constraints, audience, format, and success criteria are missing.
- Whether the user prefers direct, friendly, technical, formal, or informal language.
- Whether the user tends to ask for short answers, deep reasoning, tables, plans, or checklists.
- Whether the user tends to under-specify domain, environment, tools, or audience.
- Whether sensitive domains need stronger safety boundaries.

Verification:

- The detector can run on existing `problem_sessions`.
- Each trait has a score, confidence, and evidence.
- The output can be refreshed after new prompt activity.
- The profile does not claim more than the evidence supports.

---

## Phase 9: Chat History Import and Integration Foundation

Goal: Let PromptPilot study previous AI chats safely, starting with user-provided imports before direct platform connections.

Import paths:

```txt
paste raw chat
upload markdown
upload JSON export
upload text transcript
manual conversation entry
```

Platform adapter contract:

```txt
platform
source_type
external_conversation_id
conversation_title
message_role
message_text
message_timestamp
metadata
consent_status
redaction_status
```

Target future platforms:

- Codex
- Claude
- ChatGPT
- Gemini
- Cursor
- Windsurf
- Custom MCP tools or local transcript folders

Privacy and safety rules:

- Do not require direct account integrations for the first version.
- Let the user review imported text before analysis.
- Add redaction for obvious secrets, API keys, tokens, emails, and phone numbers.
- Provide delete and reprocess controls.
- Never expose provider tokens in frontend code.

Verification:

- Imported conversations are normalized into a common schema.
- Imported content can be analyzed into prompting traits.
- Redaction status is visible.
- Deleting an import removes its derived profile observations or marks them stale.

---

## Phase 10: Open Domain Detection and Confirmation

Goal: Replace the fixed starter-domain classifier with open domain detection and explicit user confirmation.

The current classifier is useful for the MVP, but it is tied to starter domains. Future detection should return the likely domain, subdomain, alternatives, evidence, confidence, and a confirmation requirement.

Classification response shape:

```txt
primary_domain
subdomain
intent
risk_level
confidence
evidence
alternative_domains
needs_domain_confirmation
confirmed_domain
domain_source: detected | user_confirmed | user_corrected
```

UX flow:

```txt
detect domain
-> ask "I think this is about X. Is that right?"
-> if yes, continue
-> if no, let user provide or select the correct domain
-> generate domain-aware clarifying questions
```

Verification:

- The system can classify prompts outside the original four MVP domains.
- Low-confidence or ambiguous classifications ask for domain confirmation.
- User-corrected domains are stored and used by the prompt generator.
- Profile analysis can notice recurring user domains.

---

## Phase 11: Clarification-First Prompt Refinement

Goal: Make prompt refinement feel guided instead of jumping straight to an answer.

For refinement mode, PromptPilot should ask critical questions before recommending a prompt. The user can skip questions, but the final prompt should carry assumptions and lower confidence when important context is missing.

Refinement pipeline:

```txt
raw request
-> detect and confirm domain
-> inspect profile traits
-> identify missing context
-> ask clarifying questions
-> merge answers and preferences
-> generate detailed prompt
-> explain why this prompt was recommended
```

Detailed prompt contract:

```txt
role
task
context
domain
constraints
audience
tone
formality
detail level
temperature or creativity guidance
output format
success criteria
assumptions
follow-up behavior
safety or source boundaries
```

Verification:

- Refinement mode asks questions before generating the recommendation.
- The user can answer, skip, or revise clarifying questions.
- Generated prompts include domain, constraints, format, assumptions, and success criteria.
- Recommendation explanations mention which user preferences and profile traits shaped the prompt.

---

## Phase 12: Advanced Controls and Target Platform Output

Goal: Let users shape prompts for the AI system they plan to use.

Expand the current tuner beyond length, skill level, tone, format, risk, and sources.

New controls:

```txt
target_platform: codex | claude | chatgpt | gemini | cursor | generic
detail_level: concise | balanced | exhaustive
formality: casual | neutral | formal
temperature: precise | balanced | creative
reasoning_style: direct_answer | step_by_step | ask_first | explore_options
source_strictness: none | cite_when_needed | official_only | evidence_first
interaction_mode: one_shot | iterative | agentic
```

Platform behavior:

- Codex prompts should emphasize repo context, constraints, files, verification, and expected code-change behavior.
- Claude prompts should support long-context analysis, nuanced reasoning, and careful structure.
- ChatGPT prompts should be general-purpose, explicit, and portable.
- Gemini prompts should support multimodal or broad research use cases when relevant.
- Generic prompts should avoid provider-specific assumptions.

Verification:

- Settings persist with sessions and profiles.
- Prompt output changes based on selected platform.
- The UI exposes controls ergonomically without turning into a settings wall.
- Existing prompt scoring accounts for platform fit.

---

## Phase 13: Profile Q&A and UX Dashboard

Goal: Let users ask questions about their prompting behavior and receive grounded answers.

Example user questions:

```txt
What do I usually forget to include?
Why do my prompts get vague answers?
How should I prompt Codex better?
What tone do I usually prefer?
Which domains do I ask about most?
How can I make my research prompts stronger?
```

Dashboard sections:

- Prompting profile summary.
- Trait cards with confidence and examples.
- Common missing details.
- Preferred tone, format, and detail level.
- Frequent domains and task types.
- Platform-specific advice.
- Recent prompt revisions and improvement history.

Grounding rules:

- Answers should cite profile observations or imported conversation evidence.
- If there is not enough evidence, say so and ask for more examples.
- The dashboard should help the user improve without sounding judgmental.

Verification:

- Profile Q&A can answer from stored traits.
- Answers include evidence references or confidence language.
- Empty-state guidance appears before enough data exists.
- The UX supports profile review, correction, and deletion.

---

## Phase 14: Session Onboarding, Live Evaluation, Privacy, and Production Readiness

Goal: Make PromptPilot trustworthy and useful for real users by adding a session-first onboarding layer, strict guardrails, clean-slate user data, personalized AI-platform guidance, and live evaluation metrics that protect and score the quality of each interactive prompting session.

Core product goal:

Improve how a person talks to AI.

Evaluation posture:

- Treat evaluation as a live product pipeline feature, not only a static development benchmark.
- Make `POST /sessions/{session_id}/run-pipeline` the main place where session quality is measured, scored, persisted, and returned to the frontend.
- Evaluate whether PromptPilot improves the user's raw input into a clearer, safer, platform-aware prompt contract.
- Preserve all Phase 0 through Phase 13 behavior, including local Postgres/pgvector schema support, open-domain confirmation, skipped-question assumptions, platform-aware prompt output, and `trait_detector_v1` profile trait signal detection.

Session and onboarding model:

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

Live pipeline evaluation workflow:

```txt
raw user request
-> active session profile and selected target platform
-> open-domain classification and confirmation state
-> clarifying questions, answers, skipped questions, and assumptions
-> platform-aware prompt contract generation
-> dynamic local evaluator scoring through Ollama llama3.1:8b
-> normalized score breakdown, recommendation, explanation, and recommended actions
-> persisted prompt score records and dashboard-ready API payload
```

Dynamic session evaluation criteria:

- `input_to_contract_improvement`: how much the final prompt improves the user's messy raw input into a usable AI instruction.
- `contract_completeness`: whether the prompt contract includes role, task, context, domain, constraints, audience, tone, formality, detail level, output format, success criteria, assumptions, follow-up behavior, and safety/source boundaries.
- `assumption_handling`: whether skipped or unanswered required questions are carried forward as explicit assumptions without pretending the missing context is known.
- `domain_accuracy`: whether detected, confirmed, or corrected domain context is reflected accurately in the prompt and scoring explanation.
- `clarification_value`: whether clarifying questions reduce ambiguity and improve the recommended variant.
- `platform_fit`: whether the prompt is shaped for the selected target platform, including Claude, OpenAI/ChatGPT, Codex, Gemini, Cursor, or generic assistants.
- `safety_privacy_integrity`: whether sensitive requests, secrets, imported content, and misuse attempts are handled with the correct warnings, redaction, or refusal/redirect behavior.
- `user_actionability`: whether the recommended variant and explanation help the user understand what to do next.

Ollama-backed live scoring:

- Wire the backend evaluation path to local `Ollama` with `llama3.1:8b` for dynamic scoring of generated prompt variants during `POST /sessions/{session_id}/run-pipeline`.
- Use the local model to score prompt quality improvement, contract completeness, assumptions, domain accuracy, and platform fit across the live variants.
- Normalize model output into validated fields before persistence or display, including numeric score dimensions, a recommendation label, a short explanation, and recommended user actions.
- Record the scoring model and scorer version so results can be audited and compared against future scoring changes.
- Keep deterministic rule scoring available as a local fallback only when the evaluator is unavailable, and make that fallback visible in the scorer metadata.

promptfoo regression coverage:

- Use `promptfoo` in Phase 14 to test the live scoring algorithms, not as a separate product surface.
- Add a diverse scenario suite under `evals/promptfoo` that calls the live backend workflow or an equivalent scoring harness.
- Cover messy raw prompts, skipped clarifying questions, domain ambiguity and correction, profile-trait influence, target-platform differences, sensitive domains, redaction, and prompt-injection style imported content.
- Assert that scores stay within schema, recommendations rank the strongest variant, skipped questions become assumptions, platform fit changes when the selected platform changes, unsafe requests are not recommended, and explanations remain actionable.
- Run promptfoo before Phase 14 is considered complete so scoring behavior cannot regress silently.

Evaluation coverage:

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

Production features:

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
- Export to Markdown, PDF, and JSON.
- Data reset and deletion flows that work at the session level.

App shell and personalized experience:

- Keep a constant header and footer across the workspace, profile, import, library, and settings routes.
- Make tab and route switching smooth while preserving the active session.
- Make the PromptPilot logo navigate directly to the home workspace.
- Personalize headings, recommendations, profile insights, and prompt guidance with the user's name and selected AI platform.
- Keep the UI minimal and readable.
- Avoid overwhelming users with raw scoring figures; show plain-language guidance first and move detailed metrics into expandable details.
- Route every user-facing generated output through the AI formatting layer so the result is polished for the selected AI platform.
- Do not echo the user's input back as raw labels such as `Problem: ...`; reframe and format outputs according to PromptPilot's product voice.
- Remove seeded examples, demo rows, and precreated profile data from the production session path.

Security and safety:

- PII handling rules.
- Secret redaction.
- Sensitive-domain warnings.
- Medical, legal, financial, repair, and safety boundaries where appropriate.
- Prompt injection checks for imported or retrieved external content.
- Required rules acceptance before session start.
- Strict misuse guardrails for harmful, deceptive, abusive, or policy-violating requests.
- Safe completion patterns that explain boundaries briefly and redirect to allowed help.
- No persistence of sensitive session data beyond the active session unless the user explicitly chooses an export or future account-based feature.

Planned work:

- [ ] Build the session onboarding screen and session store.
- [ ] Add display-name and AI-platform fields to the session model.
- [ ] Add the supported AI-platform list with an Other option.
- [ ] Add rules acceptance and guardrail checks before entering the workspace.
- [ ] Add Start New Session and End Session flows.
- [ ] Remove precreated examples and demo data from the default production path.
- [ ] Personalize workspace, profile, refinement, and Q&A copy around the active session.
- [ ] Extend `POST /sessions/{session_id}/run-pipeline` so live scoring is part of the backend workflow instead of a detached benchmark step.
- [ ] Add dynamic scoring dimensions for input-to-contract improvement, contract completeness, assumption handling, domain accuracy, clarification value, platform fit, safety/privacy integrity, and user actionability.
- [ ] Wire local `Ollama` with `llama3.1:8b` into the live scorer for generated prompt variants.
- [ ] Normalize and validate AI-generated score output before it is stored in `prompt_scores`, prompt variant metadata, or API responses.
- [ ] Preserve current deterministic scoring behavior as an explicit fallback with visible scorer metadata.
- [ ] Add promptfoo scenarios for diverse user requests, skipped questions, domain correction, platform-specific recommendations, sensitive prompts, redaction, and profile-trait influence.
- [ ] Use promptfoo assertions to prevent regressions in score schema, ranking, assumptions, domain fit, platform fit, safety behavior, and recommendation explanations.
- [ ] Simplify score-heavy UI so user-facing guidance is readable before raw metrics.
- [ ] Ensure all generated outputs pass through the AI formatter before display.
- [ ] Add tests for privacy-critical behaviors.
- [ ] Define session, auth, and ownership boundaries before real chat storage.
- [ ] Add export and delete flows for profile data.
- [ ] Add audit logs for model runs, imports, and evaluator/scorer runs.

Verification:

- A new visitor must create a session with name, AI platform, and rules acceptance before using the workspace.
- AI platform options include ChatGPT, Claude, Grok, Perplexity, Gemini, Copilot, Cursor, Codex, and Other.
- Session state persists across route changes and refreshes until End Session is used.
- End Session clears active local session state and returns to onboarding.
- Start New Session creates a clean slate without seeded examples, previous profile observations, imports, or prompt history.
- Header and footer remain stable across tabs and routes.
- Logo click returns to the home workspace.
- User-facing outputs are AI-formatted, personalized, and free of raw `Problem: ...` style echoes.
- Scores are readable and detailed metrics are not the dominant UI.
- `POST /sessions/{session_id}/run-pipeline` returns live evaluation fields for each generated variant.
- Dynamic scores measure prompt quality improvement, contract completeness, assumptions, domain accuracy, and platform fit.
- Skipped clarifying questions are reflected as assumptions and affect scoring confidence or specificity.
- Confirmed or corrected domains improve domain-fit scoring and explanation text.
- Local `Ollama` with `llama3.1:8b` can score live variants in local development.
- Scorer metadata identifies whether `Ollama` or the deterministic fallback produced the score.
- promptfoo scenarios cover diverse messy user inputs, target platforms, skipped questions, safety/privacy cases, and profile-trait influence.
- promptfoo regression checks pass locally.
- Guardrails block misuse and safely redirect allowed use cases.
- Evaluation suite runs locally.
- Privacy-critical behaviors have tests.
- Session, auth, and ownership boundaries are explicit before storing real user chat history.
- Users can export and delete their profile data.
- Audit logs exist for imports and model runs.
- Existing Phase 0 through Phase 13 behavior remains intact, including local Postgres/pgvector schemas and `trait_detector_v1` signal generation.

---

## Phase 15: Codebase Cleanup, AI-Formatted Outputs, Knowledge Support, and Pre-Deploy Polish

Goal: Prepare PromptPilot for Phase 16 Vercel deployment by cleaning the codebase, simplifying the product surface, documenting the architecture, and ensuring AI-generated scoring explanations, platform-fit ratings, and recommended actions are cleanly formatted for the Next.js dashboards.

Codebase cleanup:

- Remove or archive unnecessary local-only artifacts before deployment, including stale screenshots, temporary smoke-test output, outdated status notes, unused changelog drafts, and obsolete planning fragments.
- Keep the useful execution reports, but make the current status and roadmap concise enough to support deployment.
- Audit `.gitignore`, environment examples, generated files, local logs, and development-only assets.
- Remove seeded demo data paths from production startup.
- Make sure no production code depends on local-only services such as `localhost`, local Docker, or local Ollama, while preserving local Ollama as a documented development evaluator from Phase 14.
- Ensure the app can run from a clean install using documented commands and environment variables.
- Keep the implementation minimal by removing unused components, dead API routes, orphaned helpers, stale constants, and old UI copy.

README and documentation cleanup:

- Rewrite the root `README.md` so it explains the final architecture, setup, environment variables, local development, API usage, frontend routes, session model, guardrails, profile behavior, exports, and deployment path.
- Update `apps/api/README.md` with API architecture, endpoints, persistence, session data flow, safety checks, and production environment variables.
- Update `apps/web/README.md` with app shell structure, routes, session onboarding, responsive design, and build/deploy commands.
- Update execution reports so the current phase status is accurate and no stale "current status" text conflicts with the Phase 16 deployment plan.
- Document how to start, end, and reset a session.
- Document what data persists only for the active session and what can be exported.

Minimal UX and session continuity:

- Make the app visually minimal, responsive, and focused on the active session.
- Keep header and footer constant across route changes.
- Keep the logo linked to the home workspace.
- Preserve the active session until the user explicitly ends it.
- Keep all major flows accessible from the main workspace without requiring users to understand internal scores or model plumbing.
- Prefer plain-language guidance over dense dashboards.
- Hide raw scoring figures, traces, and implementation details behind optional expanded views.
- Keep mobile, tablet, and desktop layouts polished before deployment.

AI-formatted scoring output:

- Ensure AI-generated scoring explanations, platform-fit ratings, and recommended actions are cleanly formatted and safe to surface in the Next.js workspace, comparison view, profile dashboard, and future evaluation dashboards.
- Define a frontend-ready scoring contract that can include `score_total`, `score_breakdown`, `platform_fit_rating`, `recommendation_label`, `recommendation_summary`, `why_this_variant`, `assumption_notes`, `recommended_actions`, and `scorer_metadata`.
- Keep score explanations short, specific, and user-facing. They should explain why a variant is recommended for the selected platform, such as Claude versus OpenAI/ChatGPT, without exposing raw evaluator prompts or model chatter.
- Translate evaluation metrics into clear feedback about how the user's raw request improved, what assumptions remain, which domain details matter, and what action the user should take next.
- Make platform-fit guidance explicit: explain why a Claude prompt may emphasize long-context structure and nuance, why an OpenAI/ChatGPT prompt may emphasize portable explicit instructions, why a Codex prompt may emphasize repository context and verification, and why generic prompts avoid provider-specific assumptions.
- Guardrail output formatting so dashboard text never appears as raw JSON, chain-of-thought, internal scoring rubrics, unvalidated model output, or raw `Problem: ...` echoes.
- Put detailed numeric metrics behind expandable UI while leading with the recommendation, plain-language rationale, and next action.

AI-first output polish:

- Ensure every visible output that interprets or rewrites user intent goes through the AI formatting layer.
- Personalize output using the active session name and selected AI platform.
- Keep generated responses aligned with the selected AI platform's expected style.
- Remove raw echo formats such as `Problem: ...` unless they are part of a deliberate export format.
- Ensure the product voice stays consistent across workspace, profile, imports, library, exports, and Q&A.
- Include scoring explanations and recommended actions in the same formatting pass so evaluation output feels like product guidance, not a developer report.

Prompt knowledge base role:

- Store licensed prompt patterns and project-created examples only when they support personalized refinement without seeding visible demo data into new sessions.
- Track source, URL, author, license, allowed usage, domain, intent, prompt type, and quality score.
- Prefer pattern extraction and synthesis over copying.

RAG role:

- Retrieve useful prompt structures and domain patterns.
- Keep retrieved context subordinate to user settings, confirmed domain, safety rules, and profile preferences.
- Preserve license metadata.
- Ensure retrieved content cannot override the active session profile, rules acceptance, selected AI platform, or guardrails.

DSPy role:

- Structure classification, clarification, refinement, scoring, and profile Q&A modules.
- Use optimizers only after enough examples, feedback, and evaluation cases exist.
- Keep DSPy modules behind stable schemas so the UI receives polished guidance instead of raw intermediate scores.

Agent tracks role:

- Convert repeated workflows into guided tracks after the profile/refinement system is stable.
- Initial tracks can include Fix Something, Build Something, Learn Something, Write Something, Compare Options, and Research Topic.
- Keep agent tracks optional and session-aware, with the same guardrails and AI-formatting rules as the main workspace.

Verification:

- Codebase cleanup removes stale local-only artifacts, unused files, obsolete UI copy, and production-blocking assumptions.
- `README.md`, `apps/api/README.md`, and `apps/web/README.md` accurately explain architecture, setup, functionality, sessions, guardrails, and deployment.
- Current status, changelog, and phase docs do not conflict with the Phase 16 Vercel deployment plan.
- The app remains minimal, responsive, and readable on mobile, tablet, and desktop.
- Session state sticks until the user explicitly ends it.
- No seeded demo examples or precreated user data appear in a new production session.
- All user-facing interpreted outputs are AI-formatted and personalized.
- Scoring explanations, platform-fit ratings, and recommended actions are formatted for frontend display.
- Recommended variants explain why they fit the selected target platform, including Claude versus OpenAI/ChatGPT-style differences when relevant.
- Dashboard copy translates scores into actionable user feedback instead of exposing raw evaluator internals.
- Output guardrails prevent raw JSON, chain-of-thought, unvalidated evaluator text, raw `Problem: ...` echoes, and confusing score dumps from appearing in the UI.
- Knowledge sources are licensed and tracked.
- RAG outputs are synthesized rather than copied.
- DSPy modules conform to existing schemas.
- Agent tracks improve guided workflows without hiding user control.
- Retrieved content cannot override user settings, confirmed domain, safety rules, or profile preferences.
- Local lint, build, API compile, and smoke checks pass immediately before Phase 16 begins.

---

## Phase 16: Vercel Production Deployment

Goal: Take the complete PromptPilot application live on Vercel as a public, responsive production application after session onboarding, privacy, evaluation, guardrails, codebase cleanup, documentation, knowledge support, and pre-deploy polish are stable.

Deployment posture:

- Deploy the Next.js frontend and FastAPI API from the monorepo to Vercel.
- Deploy directly with the Vercel CLI from this repository; do not introduce another backend-as-a-service or deployment wrapper.
- Use separate Vercel projects for `apps/web` and `apps/api` unless Vercel Services is available and appropriate for this account.
- Keep all local-only assumptions out of production: no `localhost` API URLs, no local Docker database, and no local Ollama dependency for public traffic.
- Use a managed Postgres provider with pgvector support for production data.
- Store secrets only in Vercel environment variables or the managed provider dashboard.

Production setup:

- Install the Vercel CLI at the very end of the roadmap with `pnpm.cmd i -g vercel@latest` or `npm.cmd i -g vercel@latest`.
- Authenticate with Vercel, link the monorepo projects, and confirm project roots:
  - Web root: `apps/web`
  - API root: `apps/api`
- Configure production environment variables:
  - Web: `NEXT_PUBLIC_API_BASE_URL`
  - API: `DATABASE_URL`, `LLM_PROVIDER`, provider API keys, `DEFAULT_MODEL`, and allowed frontend origins.
- Update API CORS configuration so the production web domain and preview domains can call the API.
- Confirm the FastAPI entrypoint is Vercel-compatible and exposes an ASGI `app`.
- Confirm the frontend build uses the production API URL and remains responsive across mobile, tablet, and desktop.
- Replace local schema bootstrapping with a production-safe migration or deployment step before storing real user data.

Deployment flow:

- Run local verification first:
  - `uv --directory apps/api run python -m compileall app`
  - `pnpm.cmd --dir apps/web lint`
  - `pnpm.cmd --dir apps/web build`
- Link and configure the API project with Vercel CLI.
- Add API production secrets with Vercel environment commands or the Vercel dashboard.
- Deploy the API preview, smoke test `/` and `/health`, then promote to production.
- Link and configure the web project with Vercel CLI.
- Set `NEXT_PUBLIC_API_BASE_URL` to the production API URL.
- Deploy the web preview, test the full workflow against the production API, then deploy to production.
- Attach the public production domain and verify HTTPS.

Verification:

- Public web URL loads the working PromptPilot workspace, not a landing page.
- The application is responsive on mobile, tablet, and desktop.
- Public API `/health` returns healthy application and database status.
- Web production can create sessions, run the pipeline, answer/skip clarifying questions, save prompts, view library, refresh profile, and use imports.
- CORS allows only the intended Vercel production domain, preview domains if needed, and approved local development origins.
- Production logs are clean after smoke testing.
- Deployment URLs, environment variable names, project IDs, and rollback notes are recorded in `execution-reports/`.

---

## Initial Codex Task Checklist

Use this checklist when starting implementation:

- [x] Confirm local tool versions.
- [x] Create monorepo folder structure.
- [x] Initialize Next.js frontend.
- [x] Initialize FastAPI backend.
- [x] Add Docker Compose with Postgres/pgvector.
- [x] Add root README and env examples.
- [x] Implement health endpoint.
- [x] Implement session creation endpoint.
- [x] Implement rule-based classifier.
- [x] Implement clarifying question generator.
- [x] Implement prompt variant generator.
- [x] Implement prompt scorer.
- [x] Build main frontend workspace.
- [x] Wire frontend to backend.
- [x] Add save/copy/run actions.
- [x] Add basic prompt library page.
- [x] Add prompt compare view.
- [x] Add prompting profile foundation.
- [x] Add prompting trait detection.
- [x] Add chat history import and integration foundation.
- [x] Add open domain detection and confirmation.
- [x] Add clarification-first prompt refinement.
- [x] Add advanced controls and platform-aware prompt output.
- [x] Add profile Q&A dashboard.
- [ ] Add session onboarding, live evaluation, privacy, and production readiness.
- [ ] Add codebase cleanup, AI-formatted scoring outputs, knowledge support, RAG, DSPy, and agent tracks as support systems.
- [ ] Install Vercel CLI and deploy the complete public production application on Vercel.

---

## Current Status

Status: Phase 13 profile Q&A and UX dashboard complete.

Next recommended step:

Start Phase 14: Session Onboarding, Live Evaluation, Privacy, and Production Readiness.
