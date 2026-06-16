# PromptPilot

PromptPilot is a planned full-stack prompt intelligence platform. Its goal is to turn messy user problems into high-quality, tunable, ranked AI prompts and eventually guided agentic workflows.

Project owner: Sameer Nagar

The core promise:

> Tell us your problem. We will build the best AI request for it.

## What PromptPilot Will Do

PromptPilot is not intended to be a static prompt template library. It is designed as a dynamic prompt engine that can:

- Understand a user's messy natural-language problem.
- Detect domain, intent, risk, and likely user need.
- Ask clarifying questions when useful.
- Let the user tune style, depth, tone, risk, and output format.
- Generate multiple prompt variants.
- Score, compare, and recommend the strongest prompt.
- Let users copy, save, improve, or run prompts.
- Expand later into agent tracks, prompt packs, MCP integrations, and workflow execution.

## MVP Scope

The MVP is complete when a user can:

- Enter a messy problem.
- Get automatic domain and intent detection.
- Answer clarifying questions.
- Tune prompt settings.
- Generate at least 3 prompt variants.
- Compare scores and explanations.
- Copy or run the selected prompt.
- Save prompts to a personal library.

Initial MVP domains:

- Car and home troubleshooting
- Software and project building
- Writing and business communication
- Learning and research

## Planned Stack

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

Data and infrastructure:

- Postgres
- pgvector
- Docker Compose

AI and evaluation:

- LiteLLM
- Ollama
- DSPy
- promptfoo
- Langfuse

## Current Status

Current project status: Phase 6 frontend MVP is complete. The local environment, monorepo scaffold, local Postgres/pgvector service, FastAPI workflow, SQLAlchemy persistence, deterministic prompt pipeline, and working Next.js workspace are ready.

Completed so far:

- Product direction and execution phases are documented in `EXECUTION_LOG.md`.
- Local environment inventory and phase plans are documented under `execution-reports/`.
- GitHub remote sync has been configured.
- Phase 0 local environment setup is complete.
- Node, pnpm, Python, uv, Docker Desktop, Ollama, and the `llama3.1:8b` local model are installed or verified.
- Phase 1 monorepo scaffold is complete.
- Next.js frontend is initialized in `apps/web`.
- FastAPI backend is initialized in `apps/api`.
- Shared package, docs, scripts, datasets, evals, and infra folders are present.
- Postgres/pgvector local infrastructure is defined in `infra/docker-compose.yml`.
- API database and Ollama environment values are present in `apps/api/.env.example`.
- The `pgvector/pgvector:pg16` image pulls successfully.
- The local Postgres container starts, accepts connections, and has pgvector `0.8.2` enabled.
- Backend API skeleton modules, routers, schemas, and rule-based services are implemented.
- The API can create sessions, classify problems, ask clarifying questions, record answers, generate prompt variants, score them, run a Phase 3 stub, save prompts, and list saved prompts.
- SQLAlchemy models exist for users, sessions, clarifying questions, prompt variants, prompt scores, saved prompts, prompt sources, prompt embeddings, and domain packs.
- The API workflow now persists sessions, questions, prompt variants, scores, and saved prompts to Postgres.
- `prompt_embeddings.embedding` uses pgvector `vector(1536)` for future retrieval work.
- Prompt engine V1 can run the complete local pipeline without an external LLM.
- `POST /sessions/{session_id}/run-pipeline` classifies, asks questions, merges answers/settings, generates 3 variants, scores them, and selects a deterministic recommendation.
- All six planned prompt strategies are implemented: `diagnostic`, `beginner_step_by_step`, `expert_consultant`, `safety_first`, `comparison`, and `questions_first`.
- Frontend MVP workspace is implemented at `/`.
- Frontend routes exist for `/sessions/[id]`, `/compare/[id]`, `/library`, and `/settings`.
- The workspace can generate, compare, copy, run, save, and refresh prompt variants against the local API.

Not started yet:

- Prompt knowledge base ingestion
- Production application UI

## Planning Documents

- `EXECUTION_LOG.md`: original product definition, stack, phases, and implementation checklist.
- `execution-reports/README.md`: guide to the planning/report folder.
- `execution-reports/CURRENT_STATUS.md`: current project state.
- `execution-reports/00-environment-inventory.md`: installed local tools and environment notes.
- `execution-reports/01-raw-materials.md`: technologies, modules, screens, APIs, tables, and evaluation materials.
- `execution-reports/phases/`: phase-by-phase execution logs from Phase 0 through Phase 13.
- `execution-reports/CHANGELOG.md`: chronological record of checks, edits, commits, and sync steps.

## Next Step

The next implementation step is Phase 7: prompt knowledge base.

The current frontend is still the generated Next.js starter. The PromptPilot workspace UI begins in Phase 6.
