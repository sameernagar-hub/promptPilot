# PromptPilot Execution Reports

This folder is the project control center for PromptPilot. It tracks what has been checked, what has changed, which materials are needed, and how each phase from `EXECUTION_LOG.md` should be executed.

## Current Rule

Phase 13 profile Q&A and UX dashboard is complete. The roadmap has pivoted toward user prompting profiles, guided refinement, and live session-quality evaluation. The next implementation phase is Phase 14: Session Onboarding, Live Evaluation, Privacy, and Production Readiness. Phase 15 is now the codebase cleanup, AI-formatted scoring output, minimal UX, documentation, knowledge support, and pre-deploy polish phase. The final planned phase is Phase 16: direct Vercel deployment for the local Next.js frontend and local FastAPI backend.

## Files

- `CHANGELOG.md`: chronological record of commands, checks, and file changes.
- `CURRENT_STATUS.md`: short current-state summary and next decision point.
- `00-environment-inventory.md`: local tools, installed status, and install notes.
- `01-raw-materials.md`: technologies, packages, project files, data sources, and design materials needed.
- `phases/`: one execution plan log per phase from `EXECUTION_LOG.md`.

## Phase Status Legend

- `Not started`: no implementation work has been done.
- `Ready`: can begin with current tools/materials.
- `Blocked`: depends on missing software, credentials, data, or user decision.
- `In progress`: actively being implemented.
- `Complete`: implemented and verified.
