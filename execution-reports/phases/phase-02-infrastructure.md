# Phase 2: Infrastructure

## Goal

Add local database and service infrastructure.

## Status

Complete.

## Prerequisites

- Docker Desktop installed and available.
- Monorepo structure exists.

## Planned Files

- `infra/docker-compose.yml`
- `apps/api/.env.example`

## Implemented Files

- `infra/docker-compose.yml`
- `apps/api/.env.example` already contained the required Phase 2 values.

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

- [x] Docker Compose file validates.
- [x] Postgres container starts.
- [x] pgvector image pulls successfully.
- [x] API can read database URL from env.

## Execution Notes

Date: 2026-06-15

- Added `infra/docker-compose.yml` with a `postgres` service using `pgvector/pgvector:pg16`.
- Confirmed database name, user, password, port, and volume match the phase plan.
- Confirmed `apps/api/.env.example` already had the required database and Ollama environment values.
- Ran `docker compose -f infra\docker-compose.yml config`.
  - Result: Compose configuration validated successfully.
  - Note: Docker warned that this sandbox could not read `C:\Users\nagar\.docker\config.json`, but the command exited successfully.
- Ran the backend env-read check through uv.
  - Result: `DATABASE_URL` resolved to `postgresql://prompt_engine:prompt_engine@localhost:5432/prompt_engine`.
- Tried to start Postgres with `docker compose -f infra\docker-compose.yml up -d postgres`.
  - Result: blocked because Docker Desktop's engine was not running cleanly.
  - First sandboxed attempt could not access the Docker Engine pipe.
  - Elevated attempt reached Docker Desktop but returned a Docker API 500 while resolving `pgvector/pgvector:pg16`.
  - `docker desktop status` reported `stopped`.
  - `docker info` timed out or returned a Docker API 500.
  - Starting `com.docker.service` directly was denied by Windows service permissions.
  - Launching Docker Desktop and running `docker desktop start` did not bring the engine to a usable running state in this session.
- Checked WSL with `wsl --list --verbose`.
  - Result: Windows reported that WSL is not installed.
- Tried to install/enable WSL from this session.
  - `wsl --install --no-distribution` returned the same WSL-not-installed message.
  - `wsl.exe --install` returned the same WSL-not-installed message.
  - `dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart` failed with Error 740 because an Administrator command prompt is required.

## Runtime Commands

If setting up a new Windows machine, enable WSL/virtualization support from an Administrator PowerShell if needed:

```powershell
wsl.exe --install
```

If `wsl.exe --install` still does not enable WSL, use:

```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

Then restart Windows if requested. After Docker Desktop is running and healthy, start or inspect the local database service:

```powershell
docker desktop status
docker compose -f infra\docker-compose.yml up -d postgres
docker compose -f infra\docker-compose.yml ps
```

## Completion Notes

Date: 2026-06-15

- Continued Phase 2 after WSL was installed.
- Started Docker Desktop with `docker desktop start`.
- Verified Docker Desktop status as `running`.
- Verified Docker Engine with `docker info`.
  - Server version: `29.5.3`.
  - Backend: Docker Desktop on WSL2.
  - Kernel: `6.18.33.1-microsoft-standard-WSL2`.
- Verified WSL with `wsl --list --verbose`.
  - Result: `docker-desktop` was running on WSL version 2.
- Ran `docker compose -f infra\docker-compose.yml up -d postgres`.
  - Result: pulled `pgvector/pgvector:pg16`.
  - Result: created `postgres_data`.
  - Result: started `infra-postgres-1`.
- Ran `docker compose -f infra\docker-compose.yml ps`.
  - Result: `infra-postgres-1` was `Up` with `0.0.0.0:5432->5432/tcp`.
- Ran `pg_isready` inside the container.
  - Result: `/var/run/postgresql:5432 - accepting connections`.
- Checked pgvector availability.
  - Result: `vector` extension was available with default version `0.8.2`.
- Enabled pgvector in the local development database.
  - Command result: `CREATE EXTENSION`.
  - Installed extension: `vector 0.8.2`.
- Verified backend-side database access using the API uv environment and `apps/api/.env.example`.
  - Result: connected to database `prompt_engine` as user `prompt_engine`.
