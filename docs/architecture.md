# Architecture

PromptPilot is planned as a local-first full-stack monorepo.

- `apps/web`: Next.js workspace UI.
- `apps/api`: FastAPI prompt engine API.
- `packages/shared`: shared types and contracts.
- `infra`: local infrastructure such as Postgres and pgvector.
- `evals`: prompt quality evaluation assets.
