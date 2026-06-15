# PromptPilot

PromptPilot is a planned full-stack prompt intelligence platform. Its goal is to turn messy user problems into high-quality, tunable, ranked AI prompts and eventually guided agentic workflows.

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

This repository is currently in the planning and preparation stage.

Completed so far:

- Product direction and execution phases are documented in `EXECUTION_LOG.md`.
- Local environment inventory and phase plans are documented under `execution-reports/`.
- GitHub remote sync has been configured.

Not started yet:

- Monorepo scaffold
- Frontend app
- Backend API
- Database infrastructure
- Prompt engine implementation

## Planning Documents

- `EXECUTION_LOG.md`: original product definition, stack, phases, and implementation checklist.
- `execution-reports/README.md`: guide to the planning/report folder.
- `execution-reports/CURRENT_STATUS.md`: current project state.
- `execution-reports/00-environment-inventory.md`: installed and missing local tools.
- `execution-reports/01-raw-materials.md`: technologies, modules, screens, APIs, tables, and evaluation materials.
- `execution-reports/phases/`: phase-by-phase execution logs from Phase 0 through Phase 13.
- `execution-reports/CHANGELOG.md`: chronological record of checks, edits, commits, and sync steps.

## Next Step

The next implementation step is Phase 0: finish local environment setup by enabling or installing the missing tools, then Phase 1 can create the actual monorepo scaffold.

No application code has been scaffolded yet.
