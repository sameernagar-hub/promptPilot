# Phase 11: Agent Tracks

## Goal

Move from one-shot prompt generation to guided workflows.

## Status

Not started.

## Initial Tracks

- Fix Something
- Build Something
- Learn Something
- Write Something
- Compare Options
- Research Topic

## Track Schema

```json
{
  "id": "fix_something",
  "name": "Fix Something",
  "intake_questions": [],
  "prompt_strategies": [],
  "risk_rules": [],
  "required_outputs": [],
  "evaluation_tests": []
}
```

## Later Agent Roles

- Intake Agent
- Domain Agent
- Prompt Architect Agent
- Safety Reviewer Agent
- Prompt Scorer Agent
- Runner Agent

## Potential Tools

- CrewAI
- AutoGen
- MCP servers
- Flowise
- Dify
- Langflow

## Verification

- [ ] Tracks have stable schemas.
- [ ] Track routing works from user problem classification.
- [ ] Risk rules are track-aware.
- [ ] Agent role boundaries are clear before multi-agent execution is added.
