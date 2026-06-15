# Phase 10: Evaluation With promptfoo

## Goal

Prevent prompt quality regressions.

## Status

Not started.

## Planned File

- `evals/promptfoo/promptfooconfig.yaml`

## Test Scenarios

- Car clicks but will not start
- Sink leaking under cabinet
- React app state bug
- Difficult email to manager
- Research topic summary
- Legal letter explanation
- Workout plan request
- Insurance plan comparison

## Evaluation Checks

- Does the generated prompt ask for missing context?
- Does it include safety boundaries where needed?
- Does it specify output format?
- Does it match user skill level?
- Does it avoid fake certainty?
- Does it encourage sources when needed?

## Verification

- [ ] promptfoo config exists.
- [ ] MVP scenarios are covered.
- [ ] Evaluation can run locally.
- [ ] Regressions are visible before release.
