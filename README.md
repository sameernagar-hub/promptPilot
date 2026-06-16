# PromptPilot

PromptPilot is a planned full-stack prompting experience platform. Its goal is to understand how a user prompts, build a useful prompting profile, guide clarifying questions, and generate detailed prompts shaped for the user's domain, preferences, and target AI platform.

Project owner: Sameer Nagar

The core promise:

> Understand how you prompt. Then help you ask every AI system better.

## What PromptPilot Will Do

PromptPilot is not intended to be a static prompt template library. It is designed as a prompting intelligence layer that can:

- Understand a user's messy natural-language problem.
- Detect domain, intent, risk, and likely user need, then confirm the domain with the user.
- Ask clarifying questions before recommending a refined prompt.
- Let the user tune style, depth, tone, formality, temperature, risk, source strictness, and output format.
- Generate detailed prompt variants for the selected domain and target platform.
- Score, compare, and recommend the strongest prompt.
- Let users copy, save, improve, or run prompts.
- Study imported or connected AI chat history to identify prompting traits and patterns.
- Build a user prompting profile that can answer questions like "what do I usually miss?" or "how should I prompt Codex better?"
- Expand later into Codex, Claude, ChatGPT, Gemini, MCP, and other platform integrations.

## MVP Scope

The original MVP is complete when a user can:

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

The revised product direction removes the fixed-domain mindset after the MVP. Future phases should support open domain detection, domain confirmation, and user-supplied domain correction.

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

Current project status: Phase 8 prompting trait detection is complete. The local environment, monorepo scaffold, local Postgres/pgvector service, FastAPI workflow, SQLAlchemy persistence, deterministic prompt pipeline, working Next.js workspace, profile dashboard, and trait signal detector are ready.

Roadmap status: the plan has pivoted from a prompt knowledge base first to a user-experience-led prompting profile system. Phase 9 is now Chat History Import and Integration Foundation.

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
- Phase 7 profile foundation tables, schemas, and API route are implemented.
- `GET /profile` and `POST /profile/refresh` return a local prompting profile.
- The profile analyzer creates first-pass trait observations from existing local sessions.
- The frontend has a `/profile` dashboard with profile metrics, trait cards, confidence scores, and evidence links.
- Phase 8 adds `prompting_trait_signals` and the `trait_detector_v1` analyzer.
- Profile observations now roll up per-example signals with evidence levels and representative signal explanations.
- The `/profile` dashboard shows evidence level badges, signal counts, and signal explanations.

Not started yet:

- Chat history import and integration foundation
- Open domain detection with domain confirmation
- Clarification-first prompt refinement
- Platform-aware prompt output for Codex, Claude, ChatGPT, Gemini, and other AI systems
- Profile Q&A and prompting insight dashboard

## Planning Documents

- `EXECUTION_LOG.md`: product definition, stack, revised phases, and implementation checklist.
- `execution-reports/README.md`: guide to the planning/report folder.
- `execution-reports/CURRENT_STATUS.md`: current project state.
- `execution-reports/00-environment-inventory.md`: installed local tools and environment notes.
- `execution-reports/01-raw-materials.md`: technologies, modules, screens, APIs, tables, and evaluation materials.
- `execution-reports/phases/`: phase-by-phase execution logs from Phase 0 through Phase 15.
- `execution-reports/CHANGELOG.md`: chronological record of checks, edits, commits, and sync steps.

## Next Step

The next implementation step is Phase 9: Chat History Import and Integration Foundation.

This phase should add user-provided chat imports, transcript normalization, redaction status, and import review flows.
