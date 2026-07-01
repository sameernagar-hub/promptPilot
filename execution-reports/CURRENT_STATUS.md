# Current Status

PromptPilot has completed the Phase 15.5 product pivot into a prompt intelligence profile. The project is ready for Phase 16 final production preparation and deployment.

## Active Product Shape

- The `/` route is now the import-and-judge prompt intelligence workspace.
- Users paste or upload prompt sessions from Codex, Claude, ChatGPT, Cursor, Gemini, Markdown, JSON, or text.
- The primary action is `Judge My Prompts`.
- Reports answer: what is my prompting style, what are my prompts telling me, and how can I improve?
- Reports include style scores, behavior patterns, evidence excerpts, recommendations, platform comparisons, and a next-prompt recipe.
- The old frontend prompt generation workspace and saved prompt library were removed from active routes.
- `/sessions/{id}`, `/compare/{id}`, and `/library` redirect to `/`.

## Backend State

- FastAPI backend exists at `apps/api`.
- SQLAlchemy/Postgres persistence remains the local data store.
- `prompt_intelligence_reports` stores report headline, summary, scores, patterns, recommendations, recipe, comparisons, evidence, provider, model, status, and metadata.
- `POST /intelligence/analyze` can create-and-analyze pasted text or analyze an existing import.
- `GET /intelligence/reports`, `GET /intelligence/reports/latest`, and `GET /intelligence/reports/{report_id}` expose report history.
- Existing import/profile endpoints remain active and feed the intelligence profile.
- Legacy session/prompt-generation endpoints remain for historical data continuity and regression coverage, but are no longer the main product surface.

## Provider State

- OpenAI is now the default provider.
- Environment examples now use:
  - `LLM_PROVIDER=openai`
  - `OPENAI_API_KEY=`
  - `DEFAULT_MODEL=gpt-5.5`
- The API uses the OpenAI Responses API for prompt intelligence analysis when a server-side key is configured.
- Deterministic local analysis remains the development fallback when OpenAI is missing or unavailable.
- Real API keys must stay in ignored local env files or production secret storage.

## Frontend State

- `apps/web/src/components/prompt-intelligence-workspace.tsx` is the active first-screen experience.
- The app shell navigation now leads with Judge, Profile, Imports, and Settings.
- Profile and import routes remain available.
- Settings now shows OpenAI/default intelligence runtime values.
- No active frontend source references the removed generator workspace or saved prompt library.

## Documentation State

- Root `README.md` now describes PromptPilot as a prompt intelligence profile.
- `apps/api/README.md` documents the `/intelligence` API contract.
- `docs/product-spec.md`, `docs/architecture.md`, and `docs/prompt-engine.md` now describe import, judgment, reports, and OpenAI-backed analysis.

## Verified Local Tool State

- Node, pnpm, uv, Python, Docker Desktop, and local Postgres tooling were previously verified.
- Use `pnpm.cmd` on PowerShell because script execution policy can block `pnpm.ps1`.

## Phase 16 Readiness

Phase 16 should deploy the final FastAPI API and Next.js web app with managed production secrets and no local-only dependencies.

Required production API values:

- `APP_ENV=production`
- Managed `DATABASE_URL`
- `LLM_PROVIDER=openai`
- `OPENAI_API_KEY`
- `DEFAULT_MODEL=gpt-5.5`
- Production web origin in `ALLOWED_ORIGINS`

Required production web value:

- `NEXT_PUBLIC_API_BASE_URL`

Before deployment, run:

```powershell
uv --directory apps/api run python -m compileall app
uv --directory apps/api run python ../../evals/promptfoo/phase14_regression.py
pnpm.cmd --dir apps/web lint
pnpm.cmd --dir apps/web build
```
