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

App routes:

- `/`: main prompt workspace
- `/sessions/[id]`: session workspace
- `/compare/[id]`: comparison workspace
- `/library`: saved prompt library
- `/profile`: prompting profile dashboard
- `/profile/imports`: chat import review workflow
- `/settings`: model and runtime settings

The `/profile` dashboard shows profile metrics, trait cards, evidence level badges, signal counts, representative signals, and evidence links.

The `/` workspace now focuses on a guided flow: request, Refine/Quick mode selection, domain confirmation, clarifying questions with answer/skip/revise states, one full platform-aware recommended prompt, assumptions, revision history, optional alternatives, grouped preferences, profile-seeded platform defaults, and theme selection.

The `/profile/imports` workflow supports platform/source selection, transcript entry, file upload, import ledger review, redaction status, redacted message preview, reprocess, and delete.

Verification:

```powershell
pnpm.cmd --dir apps/web lint
pnpm.cmd --dir apps/web build
```
