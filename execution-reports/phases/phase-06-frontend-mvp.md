# Phase 6: Frontend MVP

## Goal

Build a usable app as the first screen, not a landing page.

## Status

Not started.

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

- [ ] First screen is the working product.
- [ ] User can enter a problem.
- [ ] User can answer clarifying questions.
- [ ] User can tune prompt settings.
- [ ] Prompt variants display with scores.
- [ ] Copy, run, save, compare, and refresh actions are represented.
