# Phase 2: Infrastructure

## Goal

Add local database and service infrastructure.

## Status

Not started.

## Prerequisites

- Docker Desktop installed and available.
- Monorepo structure exists.

## Planned Files

- `infra/docker-compose.yml`
- `apps/api/.env.example`

## Planned Services

- Postgres using `pgvector/pgvector:pg16`.
- Database name: `prompt_engine`.
- Database user: `prompt_engine`.
- Database password: `prompt_engine`.
- Port: `5432`.
- Volume: `postgres_data`.

## Backend Environment Variables

```txt
DATABASE_URL=postgresql://prompt_engine:prompt_engine@localhost:5432/prompt_engine
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=ollama/llama3.1:8b
```

## Optional Later Services

- Langfuse
- LiteLLM proxy
- Qdrant
- Chroma

## Verification

- [ ] Docker Compose file validates.
- [ ] Postgres container starts.
- [ ] pgvector image pulls successfully.
- [ ] API can read database URL from env.
