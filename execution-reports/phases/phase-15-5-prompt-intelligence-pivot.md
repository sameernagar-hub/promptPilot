# Phase 15.5 Prompt Intelligence Pivot

Status: Complete

## Goal

Pivot PromptPilot away from prompt generation and toward prompt behavior recognition, scoring, and improvement.

## Completed

- Replaced the main frontend route with a prompt intelligence workspace.
- Added paste/upload import as the first-screen workflow.
- Added `Judge My Prompts` as the primary action.
- Added prompt intelligence report persistence in `prompt_intelligence_reports`.
- Added `/intelligence` API endpoints for creating and reading reports.
- Integrated OpenAI as the default provider through `LLM_PROVIDER=openai`, `OPENAI_API_KEY`, and `DEFAULT_MODEL=gpt-5.5`.
- Preserved deterministic local analysis as the fallback when OpenAI is unavailable.
- Removed active frontend generator routes and deleted the old generator workspace component.
- Updated root README, API README, product spec, architecture doc, prompt-engine doc, changelog, and current status.

## Phase 16 Handoff

Phase 16 should deploy the prompt intelligence product, not the former prompt generator.

Required production configuration:

- `APP_ENV=production`
- Managed `DATABASE_URL`
- `LLM_PROVIDER=openai`
- `OPENAI_API_KEY`
- `DEFAULT_MODEL=gpt-5.5`
- Production web origin in `ALLOWED_ORIGINS`
- Web `NEXT_PUBLIC_API_BASE_URL`

Real API keys must be stored only in ignored local env files or managed production secrets.
