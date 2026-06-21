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

The `/profile` dashboard shows profile metrics, profile Q&A, suggested questions, missing-detail insights, preferences, frequent domains, platform advice, recent revisions, trait cards, evidence level badges, signal counts, representative signals, evidence links, correction controls, and hide controls.

The `/` workspace now opens behind a Phase 14 session-start flow. A visitor must provide a display name, select a primary AI platform, and accept rules before the workspace is usable. The active session profile is stored locally until End Session is used.

The `/` workspace now focuses on a guided flow: session onboarding, request entry, optional agent-track selection, Refine/Quick mode selection, domain confirmation, clarifying questions with answer/skip/revise states, one full platform-aware recommended prompt, assumptions, revision history, optional alternatives, grouped preferences, profile-seeded platform defaults, and theme selection.

Workspace behavior:

- Supported primary AI platforms: ChatGPT, Claude, Grok, Perplexity, Gemini, Copilot, Cursor, Codex, and Other.
- Optional agent tracks are available for Fix, Build, Learn, Write, Compare, and Research. They merge ordinary workspace preferences and add an `agent_track` session metadata hint without hiding user control.
- Start New Session resets the current request, answers, prompt output, assumptions, and run output without reusing seeded examples.
- End Session clears the local active session and returns to onboarding.
- Export downloads the active session as Markdown.
- Delete removes the active backend session data after confirmation.
- The PromptPilot logo links back to `/`.
- Generated prompt metrics stay secondary behind collapsed evaluation details.
- Evaluation details expose score breakdowns, platform-fit ratings, modification audit trails, skipped-question assumptions, matched rules, trait alignment, optimization paths, recommended actions, and scorer metadata.
- Guardrail-blocked requests display a short boundary message and a safe redirect instead of prompt variants.
- Shared header/footer framing is stable across workspace, onboarding, profile, imports, library, and settings.
- The `/profile` page includes low-profile export and derived-profile reset controls.

The `/profile/imports` workflow supports platform/source selection, transcript entry, file upload, import ledger review, redaction status, redacted message preview, reprocess, and delete.

Verification:

```powershell
pnpm.cmd --dir apps/web lint
pnpm.cmd --dir apps/web build
pnpm.cmd --dir apps/web start
```

Local development and local production-build smoke checks both use the frontend port `3000`; stop the dev server before running `pnpm.cmd --dir apps/web start`. The API should only allow `http://localhost:3000` and `http://127.0.0.1:3000` for local CORS.
