# PromptPilot Web

Next.js frontend for the PromptPilot prompt intelligence profile.

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

## Active Routes

- `/`: prompt intelligence import-and-judge workspace.
- `/profile`: prompt intelligence profile dashboard.
- `/profile/imports`: import ledger and redacted preview workflow.
- `/settings`: runtime and model settings.

The old prompt generation routes now redirect to `/`:

- `/sessions/[id]`
- `/compare/[id]`
- `/library`

## Main Screen

The `/` route lets the user:

- Select the source platform.
- Paste or upload a Markdown, JSON, text, or transcript-style prompt session.
- Click `Judge My Prompts`.
- Review the latest prompt intelligence report.
- See style scores, behavior patterns, evidence excerpts, recommendations, comparisons, import ledger, and report history.

## Verification

```powershell
pnpm.cmd --dir apps/web lint
pnpm.cmd --dir apps/web build
pnpm.cmd --dir apps/web start
```

Local development and local production-build smoke checks both use the frontend port `3000`; stop the dev server before running `pnpm.cmd --dir apps/web start`.
