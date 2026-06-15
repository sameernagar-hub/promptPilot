# Phase 0: Local Environment Setup

## Goal

Prepare local development tools.

## Status

Blocked until missing tools are installed or enabled.

## Verified

- Node is installed: `v24.16.0`.
- npm is installed: `11.13.0` through `npm.cmd`.
- Corepack is installed: `0.35.0`.
- uv is installed: `0.11.18`.

## Missing or Not Usable

- pnpm is not found on PATH.
- Python runtime is not installed or not usable.
- Docker is not found on PATH.
- Ollama is not found on PATH.

## Required Actions

- [ ] Install or enable pnpm.
- [ ] Install Python 3.10+.
- [ ] Install Docker Desktop.
- [ ] Install Ollama.
- [ ] Pull `llama3.1:8b` with Ollama.
- [ ] Re-run all version checks and update `00-environment-inventory.md`.

## Commands From Execution Log

```bash
node --version
pnpm --version
python --version
uv --version
docker --version
ollama --version
npm install -g pnpm
pip install uv
ollama pull llama3.1:8b
```

## Execution Notes

- Use `npm.cmd` instead of `npm` in PowerShell unless the execution policy is changed.
- Do not install anything until the user approves starting Phase 0.
