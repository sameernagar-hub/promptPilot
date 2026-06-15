# Phase 0: Local Environment Setup

## Goal

Prepare local development tools.

## Status

Complete.

## Verified

- Node is installed: `v24.16.0`.
- npm is installed: `11.13.0` through `npm.cmd`.
- Corepack is installed: `0.35.0`.
- uv is installed: `0.11.18`.
- pnpm is installed: `11.6.0` through `pnpm.cmd`.
- Python is installed: `Python 3.14.5`.
- uv-managed Python is installed and verified: `Python 3.12.13`.
- Docker Desktop is installed.
- Docker CLI is verified directly: Docker `29.5.3`, build `d1c06ef`.
- Ollama is installed and verified directly: `0.30.6`.
- Local Ollama model is pulled and listed: `llama3.1:8b`, `4.9 GB`.

## Required Actions

- [x] Install or enable pnpm.
- [x] Install Python 3.10+.
- [x] Install Docker Desktop.
- [x] Install Ollama.
- [x] Pull `llama3.1:8b` with Ollama.
- [x] Re-run all version checks and update `00-environment-inventory.md`.

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
- Use `pnpm.cmd` instead of `pnpm` in PowerShell unless the execution policy is changed.
- Corepack could not enable pnpm because it tried to write shims into `C:\Program Files\nodejs`; pnpm was installed successfully with `npm.cmd install -g pnpm`.
- Docker and Ollama were installed successfully and persisted PATH entries are present. This Codex session inherited PATH before installation; open a new terminal or use direct executable paths inside this session.
- Docker executable verified at `C:\Program Files\Docker\Docker\resources\bin\docker.exe`.
- Ollama executable verified at `C:\Users\nagar\AppData\Local\Programs\Ollama\ollama.exe`.
