# Architecture

PromptPilot is a local-first full-stack monorepo that is ready for production deployment once Phase 16 environment values are set.

- `apps/web`: Next.js prompt intelligence UI. The `/` route is the import-and-judge workspace.
- `apps/api`: FastAPI service for imports, prompt intelligence reports, profile traits, and health checks.
- `packages/shared`: shared TypeScript package boundary for future contracts.
- `infra`: local Postgres and pgvector support.
- `evals`: regression and evaluation assets.
- `execution-reports`: phase status, verification notes, and deployment readiness history.

## Data Flow

1. The frontend posts pasted/uploaded prompt session content to `POST /intelligence/analyze`.
2. The API creates or loads a `conversation_import`.
3. The import normalizer parses transcript, Markdown-ish, JSON, and message-list shapes.
4. Secret redaction runs before content is shown in previews.
5. The profile analyzer refreshes trait signals from imported user prompts.
6. The prompt intelligence service builds a report through OpenAI when configured, otherwise deterministic local analysis.
7. The report is stored in `prompt_intelligence_reports`.
8. The frontend renders the latest report, style scores, evidence, recommendations, import ledger, and report history.

## Provider Strategy

OpenAI is the default provider:

- `LLM_PROVIDER=openai`
- `OPENAI_API_KEY`
- `DEFAULT_MODEL=gpt-5.5`

The legacy Ollama configuration remains only as a fallback/compatibility path. Production must not depend on local Ollama.
