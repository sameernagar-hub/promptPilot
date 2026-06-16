# PromptPilot Web

Next.js frontend for the PromptPilot workspace.

Run from the repository root:

```powershell
pnpm.cmd --dir apps/web dev
```

Local URL:

```txt
http://127.0.0.1:3000
```

The frontend expects the API at:

```txt
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Phase 6 routes:

- `/`: main prompt workspace
- `/sessions/[id]`: session workspace
- `/compare/[id]`: comparison workspace
- `/library`: saved prompt library
- `/settings`: model and runtime settings

Verification:

```powershell
pnpm.cmd --dir apps/web lint
pnpm.cmd --dir apps/web build
```
