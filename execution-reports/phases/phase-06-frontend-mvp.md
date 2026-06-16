# Phase 6: Frontend MVP

## Goal

Build a usable app as the first screen, not a landing page.

## Status

Complete.

## Planned Routes

- `/`: main workspace
- `/sessions/[id]`: session detail
- `/compare/[id]`: prompt comparison view
- `/library`: saved prompt library
- `/settings`: model and user settings

## Main Workspace Layout

- Left: problem input and clarifying question form.
- Center: prompt variant cards.
- Right: tuner panel.
- Bottom or side: generation timeline.

## Planned Components

- `ProblemInput`
- `DomainBadge`
- `ClarifyingQuestions`
- `PromptTuner`
- `PromptCard`
- `PromptScoreBars`
- `PromptCompareGrid`
- `AgentTimeline`
- `RunPromptPanel`
- `SavedPromptList`
- `ModelSelector`

## Icon Set

- `Copy`
- `Play`
- `Save`
- `RefreshCw`
- `SlidersHorizontal`
- `GitCompare`
- `Sparkles`
- `ShieldCheck`

## Design Direction

- Clean workspace UI.
- No generic landing page during MVP.
- Prompt cards with score bars.
- Side-by-side compare mode.
- Tuner controls with sliders, segmented controls, toggles, and select menus.
- Timeline showing Classified -> Questions -> Generated -> Scored -> Ready.

## Verification

- [x] First screen is the working product.
- [x] User can enter a problem.
- [x] User can answer clarifying questions.
- [x] User can tune prompt settings.
- [x] Prompt variants display with scores.
- [x] Copy, run, save, compare, and refresh actions are represented.

## Implemented Routes

- `/`: main workspace
- `/sessions/[id]`: session detail workspace
- `/compare/[id]`: prompt comparison workspace
- `/library`: saved prompt library
- `/settings`: model and runtime settings

## Implemented Components

- `PromptWorkspace`
- `DomainBadge`
- `ClarifyingQuestions`
- `PromptTuner`
- `PromptCard`
- `PromptScoreBars`
- `PromptCompareGrid`
- `AgentTimeline`
- `RunPromptPanel`
- `SavedLibrary`
- `SettingsView`

## Implementation Notes

Date: 2026-06-15

- Replaced the generated Next.js starter page with the PromptPilot workspace.
- Added `apps/web/src/lib/api.ts` for typed API calls to the FastAPI backend.
- Added the main cockpit-style workspace in `apps/web/src/components/prompt-workspace.tsx`.
- Added saved prompt library and settings views.
- Added planned routes under the Next.js app router.
- Added frontend actions for:
  - problem entry
  - tuner changes
  - prompt generation
  - answering clarifying questions
  - refresh/regeneration
  - compare mode
  - copy prompt
  - run prompt
  - save prompt
  - saved prompt library browsing
- Added FastAPI CORS middleware for local frontend development origins:
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
- Design notes:
  - First screen is the product workspace, not a landing page.
  - Layout uses left intake, center prompt variants, right tuner/timeline.
  - Prompt cards include score bars and recommendation labels.
  - UI uses lucide icons for the planned actions.
  - The palette is restrained but uses green, amber, rose, and neutral tones rather than a single hue.

## Verification Notes

- Ran `pnpm.cmd --dir apps/web lint`.
  - Result: passed.
- Ran `pnpm.cmd --dir apps/web build`.
  - Result: passed.
  - Routes generated:
    - `/`
    - `/compare/[id]`
    - `/library`
    - `/sessions/[id]`
    - `/settings`
- Ran backend verification after CORS changes.
  - `uv run python -m compileall app` passed from `apps/api`.
  - `uv --directory apps/api run python main.py` passed.
- Restarted local dev servers.
  - API: `http://127.0.0.1:8000`
  - Web: `http://127.0.0.1:3000`
- Browser verification:
  - The in-app browser surface was unavailable in this session.
  - Used temporary Playwright verification against local Microsoft Edge.
  - Verified the workspace loads and shows API status.
  - Verified problem entry and tuner control selection.
  - Verified generation returns prompt variants and scores.
  - Verified clarifying answers can be entered and refreshed.
  - Verified compare mode.
  - Verified run action returns the current run stub.
  - Verified save action and `/library` display the saved prompt.
  - Inspected generated workspace and library screenshots.
- During browser verification, found and fixed a backend refresh bug.
  - Cause: replacing clarifying questions deleted and reinserted rows in one flush, violating the unique `(session_id, question_key)` index.
  - Fix: delete existing question rows and flush before inserting replacements.
