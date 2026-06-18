# Phase 16: Vercel Production Deployment

## Goal

Take the complete PromptPilot application live on Vercel as a public, responsive production application after session onboarding, privacy, evaluation, guardrails, codebase cleanup, documentation, knowledge support, and pre-deploy polish are stable.

## Status

Not started.

## Deployment Posture

- Deploy the Next.js frontend and FastAPI API from the monorepo to Vercel.
- Deploy directly with the Vercel CLI from this repository; do not introduce another backend-as-a-service or deployment wrapper.
- Use separate Vercel projects for `apps/web` and `apps/api` unless Vercel Services is available and appropriate for this account.
- Keep production independent from local-only services:
  - No `localhost` API URL in production.
  - No local Docker database in production.
  - No local Ollama dependency for public traffic.
- Use a managed Postgres provider with pgvector support for production data.
- Store secrets only in Vercel environment variables or the managed provider dashboard.

## Vercel Setup

- Install Vercel CLI at the very end of the roadmap:
  - `pnpm.cmd i -g vercel@latest`
  - or `npm.cmd i -g vercel@latest`
- Authenticate:
  - `vercel login`
- Link the monorepo projects:
  - Web project root: `apps/web`
  - API project root: `apps/api`
- Confirm project settings:
  - Web framework: Next.js
  - Web install/build commands use pnpm.
  - API framework/runtime: FastAPI through Vercel Python runtime.
  - API entrypoint exposes an ASGI `app`.
- Pull Vercel project settings locally before final testing:
  - `vercel pull`

## Production Environment Variables

Web project:

- `NEXT_PUBLIC_API_BASE_URL`: production API URL.

API project:

- `DATABASE_URL`: managed production Postgres connection string.
- `LLM_PROVIDER`: hosted provider for production traffic.
- `DEFAULT_MODEL`: production default model.
- Provider API keys as needed.
- Allowed frontend origins for CORS.

Rules:

- Do not commit production secrets.
- Keep `.env.example` as a non-secret template only.
- Confirm preview and production environments have the correct values.

## Required Application Changes

- Make API CORS environment-driven so production web and preview URLs can call the API.
- Confirm the FastAPI entrypoint works with Vercel's Python runtime from `apps/api`.
- Confirm the frontend reads the production API URL from `NEXT_PUBLIC_API_BASE_URL`.
- Replace local schema bootstrapping with a production-safe migration or release step before storing real user data.
- Confirm the public application remains responsive across mobile, tablet, and desktop routes.
- Confirm local-only model behavior has a hosted-production fallback.

## Deployment Flow

- Run local verification:
  - `uv --directory apps/api run python -m compileall app`
  - `pnpm.cmd --dir apps/web lint`
  - `pnpm.cmd --dir apps/web build`
- Deploy API preview:
  - Link the API Vercel project.
  - Add API environment variables.
  - Run `vercel deploy` from the API project root.
  - Smoke test `/` and `/health`.
- Deploy API production:
  - Run `vercel deploy --prod` from the API project root.
  - Record the production API URL.
- Deploy web preview:
  - Link the web Vercel project.
  - Set `NEXT_PUBLIC_API_BASE_URL` to the production API URL.
  - Run `vercel deploy` from the web project root.
  - Test the full app workflow against the production API.
- Deploy web production:
  - Run `vercel deploy --prod` from the web project root.
  - Attach the public production domain.
  - Confirm HTTPS.

## Verification

- [ ] Public web URL loads the working PromptPilot workspace.
- [ ] The application is responsive on mobile, tablet, and desktop.
- [ ] Public API `/health` returns healthy application and database status.
- [ ] Web production can create sessions and run the prompt pipeline.
- [ ] Clarifying question answer, skip, and revise controls work in production.
- [ ] Prompt save and library flows work in production.
- [ ] Profile refresh works in production.
- [ ] Import create, preview, reprocess, and delete flows work in production.
- [ ] CORS allows only intended production, preview, and approved local origins.
- [ ] Production logs are clean after smoke testing.
- [ ] Deployment URLs, environment variable names, project IDs, and rollback notes are recorded in `execution-reports/`.
