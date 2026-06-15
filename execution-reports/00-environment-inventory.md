# Environment Inventory

This file tracks local applications and command-line tools needed for the PromptPilot project.

## Already Installed or Available

| Tool | Status | Verified Result | Notes |
| --- | --- | --- | --- |
| Node.js | Installed | `v24.16.0` | Available as `node`. |
| npm | Installed | `11.13.0` | Use `npm.cmd` in PowerShell. |
| Corepack | Installed | `0.35.0` | Can potentially enable package managers. |
| uv | Installed | `0.11.18` | Available at `C:\Users\nagar\.local\bin\uv.exe`. |

## Missing or Not Usable Yet

| Tool | Status | Why It Matters | Recommended Action |
| --- | --- | --- | --- |
| pnpm | Missing | Frontend monorepo/package workflow in the execution log uses pnpm. | Install with npm or enable through Corepack. |
| Python | Missing/not usable | FastAPI backend requires Python 3.10+. | Install Python 3.10+ or configure an existing Python runtime. |
| Docker | Missing from PATH | Required for Postgres/pgvector local infrastructure. | Install Docker Desktop or add Docker CLI to PATH if already installed. |
| Ollama | Missing from PATH | Local LLM development target. | Install Ollama and pull `llama3.1:8b`. |

## PowerShell Notes

PowerShell cannot run `npm.ps1` because scripts are disabled by execution policy. `npm.cmd` works and should be used for now.

## Phase 0 Checklist

- [x] Check Node.
- [x] Check npm.
- [x] Check Corepack.
- [x] Check uv.
- [x] Check pnpm.
- [x] Check Python.
- [x] Check Docker.
- [x] Check Ollama.
- [ ] Install or enable pnpm.
- [ ] Install Python 3.10+.
- [ ] Install Docker Desktop.
- [ ] Install Ollama.
- [ ] Pull local model `llama3.1:8b`.
