# PromptPilot Execution Log

Project name: PromptPilot
Project purpose: Build a full-stack prompt intelligence platform that turns messy user problems into high-quality, tunable, ranked AI prompts and eventually agentic workflows.

Created by: Codex
Initial project folder: Downloads/promptPilot

---

## Product Definition

PromptPilot is not a static prompt template library. It is a dynamic prompt engine.

Core idea:

1. User describes a problem in natural language.
2. The system detects the domain, intent, risk, and likely user need.
3. The system asks clarifying questions when needed.
4. The user tunes the prompt style and constraints.
5. The engine generates multiple prompt variants.
6. The variants are scored, compared, and recommended.
7. The user can copy, save, improve, or run the prompt through an AI model.
8. Later phases expand this into agent tracks, prompt packs, MCP integrations, and workflow execution.

Primary promise:

Tell us your problem. We will build the best AI request for it.

---

## Target MVP

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

## Phase 7: Prompt Knowledge Base

Goal: Use existing free/open prompt resources without becoming a copy-paste template library.

Important rule:

Only ingest prompts that are open-source, user-submitted, explicitly licensed, or generated by the project. Do not scrape paid/private prompt libraries.

Pipeline:

```txt
import source prompts
-> normalize fields
-> remove duplicates
-> classify/tag domain and intent
-> generate embeddings
-> store source/license metadata
-> make retrievable by semantic search
```

Suggested sources:

- PromptSource by BigScience
- Project-created prompt examples
- User-submitted prompts with clear license/permission
- Public domain or permissively licensed examples

Metadata to track:

```txt
source_name
source_url
license
author
allowed_usage
domain
intent
prompt_type
quality_score
```

---

## Phase 8: Retrieval-Augmented Prompt Generation

Goal: Make generation use the prompt knowledge base.

Pipeline:

```txt
user problem
-> classify problem
-> search similar prompt patterns
-> extract reusable structures
-> synthesize new prompt variants
-> apply tuner settings
-> score and recommend
```

Do not directly copy retrieved prompts unless licensing allows it. Prefer pattern extraction and synthesis.

---

## Phase 9: DSPy Integration

Goal: Make the prompt engine structured and optimizable.

Suggested DSPy signatures:

```python
class ClassifyProblem(dspy.Signature):
    problem = dspy.InputField()
    domain = dspy.OutputField()
    intent = dspy.OutputField()
    risk_level = dspy.OutputField()

class GenerateClarifyingQuestions(dspy.Signature):
    problem = dspy.InputField()
    domain = dspy.InputField()
    intent = dspy.InputField()
    questions = dspy.OutputField()

class GeneratePromptVariants(dspy.Signature):
    problem = dspy.InputField()
    domain = dspy.InputField()
    settings = dspy.InputField()
    retrieved_patterns = dspy.InputField()
    variants = dspy.OutputField()

class ScorePromptVariant(dspy.Signature):
    problem = dspy.InputField()
    prompt_text = dspy.InputField()
    settings = dspy.InputField()
    score = dspy.OutputField()
    explanation = dspy.OutputField()
```

Use DSPy optimizers after collecting examples and ratings.

---

## Phase 10: Evaluation With promptfoo

Goal: Prevent quality regressions.

Create `evals/promptfoo/promptfooconfig.yaml`.

Test scenarios:

```txt
Car clicks but will not start
Sink leaking under cabinet
React app state bug
Difficult email to manager
Research topic summary
Legal letter explanation
Workout plan request
Insurance plan comparison
```

Evaluation checks:

```txt
Does the generated prompt ask for missing context?
Does it include safety boundaries where needed?
Does it specify output format?
Does it match user skill level?
Does it avoid fake certainty?
Does it encourage sources when needed?
```

---

## Phase 11: Agent Tracks

Goal: Move from one-shot prompt generation to guided workflows.

Initial tracks:

```txt
Fix Something
Build Something
Learn Something
Write Something
Compare Options
Research Topic
```

Track schema:

```json
{
  "id": "fix_something",
  "name": "Fix Something",
  "intake_questions": [],
  "prompt_strategies": [],
  "risk_rules": [],
  "required_outputs": [],
  "evaluation_tests": []
}
```

Later agent roles:

```txt
Intake Agent
Domain Agent
Prompt Architect Agent
Safety Reviewer Agent
Prompt Scorer Agent
Runner Agent
```

Potential tools:

- CrewAI
- AutoGen
- MCP servers
- Flowise/Dify/Langflow for visual flow editing

---

## Phase 12: Production Features

Goal: Turn MVP into a scalable product.

Add:

```txt
Authentication
User accounts
Prompt history
Prompt versioning
Prompt feedback and ratings
Public/private prompt packs
Admin review panel
Rate limits
Model usage and cost tracking
Export to Markdown, PDF, JSON
Team/workspace support
```

Security and safety:

```txt
License tracking for prompt sources
PII handling rules
Sensitive-domain warnings
Safe repair/medical/legal/financial disclaimers where appropriate
Prompt injection checks for retrieved external content
Audit logs for model runs
```

---

## Phase 13: UI Polish

Goal: Make it feel excellent.

Signature UI elements:

```txt
Prompt cockpit workspace
Live prompt preview
Side-by-side compare mode
Score bars
Prompt DNA tags: domain, strategy, risk, depth, format
Agent timeline
Why this prompt? panel
Run result drawer
Saved/remix prompt actions
```

UX principle:

The first screen should be the working product. Avoid a generic landing page during MVP.

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
- [ ] Add tests/evals.
- [ ] Add DSPy integration.
- [ ] Add prompt knowledge base ingestion.
- [ ] Add retrieval-augmented generation.
- [ ] Add agent tracks.

---

## Current Status

Status: Phase 6 frontend MVP complete.

Next recommended step:

Start Phase 7: prompt knowledge base.
