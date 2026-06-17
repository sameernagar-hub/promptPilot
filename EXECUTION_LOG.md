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

## Phase 14: Evaluation, Privacy, and Production Readiness

Goal: Make the new profile and refinement system trustworthy enough for real user data.

Evaluation coverage:

```txt
trait detection accuracy
domain detection and confirmation
clarifying question quality
refined prompt completeness
platform-specific prompt fit
profile Q&A grounding
redaction behavior
deletion and reprocessing behavior
```

Production features:

- Authentication.
- User-owned profiles.
- Prompt and import history.
- Prompt versioning.
- Feedback and ratings.
- Rate limits.
- Model usage and cost tracking.
- Audit logs for model runs and imports.
- Export to Markdown, PDF, and JSON.

Security and safety:

- PII handling rules.
- Secret redaction.
- Sensitive-domain warnings.
- Medical, legal, financial, repair, and safety boundaries where appropriate.
- Prompt injection checks for imported or retrieved external content.

Verification:

- Evaluation suite runs locally.
- Privacy-critical behaviors have tests.
- Auth and ownership are explicit before storing real user chat history.
- Users can export and delete their profile data.

---

## Phase 15: Knowledge Base, RAG, DSPy, and Agent Tracks

Goal: Bring back the old knowledge base, RAG, DSPy, and agent-track ideas as support systems for the user-profile product.

Prompt knowledge base role:

- Store licensed prompt patterns and project-created examples.
- Track source, URL, author, license, allowed usage, domain, intent, prompt type, and quality score.
- Prefer pattern extraction and synthesis over copying.

RAG role:

- Retrieve useful prompt structures and domain patterns.
- Keep retrieved context subordinate to user settings, confirmed domain, safety rules, and profile preferences.
- Preserve license metadata.

DSPy role:

- Structure classification, clarification, refinement, scoring, and profile Q&A modules.
- Use optimizers only after enough examples, feedback, and evaluation cases exist.

Agent tracks role:

- Convert repeated workflows into guided tracks after the profile/refinement system is stable.
- Initial tracks can include Fix Something, Build Something, Learn Something, Write Something, Compare Options, and Research Topic.

Verification:

- Knowledge sources are licensed and tracked.
- RAG outputs are synthesized rather than copied.
- DSPy modules conform to existing schemas.
- Agent tracks improve guided workflows without hiding user control.

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
- [ ] Add clarification-first prompt refinement.
- [ ] Add advanced controls and platform-aware prompt output.
- [ ] Add profile Q&A dashboard.
- [ ] Add privacy, evaluation, and production readiness.
- [ ] Add knowledge base, RAG, DSPy, and agent tracks as support systems.

---

## Current Status

Status: Phase 10 open domain detection and confirmation complete.

Next recommended step:

Start Phase 11: Clarification-First Prompt Refinement.
