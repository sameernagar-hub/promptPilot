# Environment Inventory

This file tracks local applications and command-line tools needed for the PromptPilot project.

## Already Installed or Available

| Tool | Status | Verified Result | Notes |
| --- | --- | --- | --- |
| Node.js | Installed | `v24.16.0` | Available as `node`. |
| npm | Installed | `11.13.0` | Use `npm.cmd` in PowerShell. |
| Corepack | Installed | `0.35.0` | Can potentially enable package managers. |
| uv | Installed | `0.11.18` | Available at `C:\Users\nagar\.local\bin\uv.exe`. |
| pnpm | Installed | `11.6.0` | Use `pnpm.cmd` in PowerShell because `pnpm.ps1` is blocked by execution policy. |
| Python | Installed | `Python 3.14.5`; `uv` Python `3.12.13` | `python --version` works outside the sandbox; `uv run --python 3.12 python --version` verified the stable backend runtime. |
| Docker Desktop | Installed | Docker CLI `29.5.3`, build `d1c06ef` | Installed at `C:\Program Files\Docker\Docker\resources\bin\docker.exe`; persisted PATH includes Docker. |
| Ollama | Installed | `0.30.6` | Installed at `C:\Users\nagar\AppData\Local\Programs\Ollama\ollama.exe`; persisted PATH includes Ollama. |
| Ollama model | Pulled | `llama3.1:8b`, `4.9 GB` | Verified with `ollama list` through the installed executable path. |

## PowerShell Notes

PowerShell cannot run `npm.ps1` or `pnpm.ps1` because scripts are disabled by execution policy. Use `npm.cmd` and `pnpm.cmd` for now.

Docker and Ollama installed successfully and persisted PATH entries are present. This Codex session inherited PATH before installation, so either open a new terminal or use these direct paths inside the current session:

```powershell
& 'C:\Program Files\Docker\Docker\resources\bin\docker.exe' --version
& 'C:\Users\nagar\AppData\Local\Programs\Ollama\ollama.exe' --version
```

## Phase 0 Checklist

- [x] Check Node.
- [x] Check npm.
- [x] Check Corepack.
- [x] Check uv.
- [x] Check pnpm.
- [x] Check Python.
- [x] Check Docker.
- [x] Check Ollama.
- [x] Install or enable pnpm.
- [x] Install Python 3.10+.
- [x] Install Docker Desktop.
- [x] Install Ollama.
- [x] Pull local model `llama3.1:8b`.
