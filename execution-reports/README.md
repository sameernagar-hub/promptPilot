# PromptPilot Execution Reports

This folder is the project control center for PromptPilot. It tracks what has been checked, what has changed, which materials are needed, and how each phase from `EXECUTION_LOG.md` should be executed.

## Current Rule

Planning artifacts only have been created. Do not scaffold, install, initialize, or generate application code until the user gives the next instruction.

## Files

- `CHANGELOG.md`: chronological record of commands, checks, and file changes.
- `CURRENT_STATUS.md`: short current-state summary and next decision point.
- `00-environment-inventory.md`: local tools, installed status, missing applications, and install notes.
- `01-raw-materials.md`: technologies, packages, project files, data sources, and design materials needed.
- `phases/`: one execution plan log per phase from `EXECUTION_LOG.md`.

## Phase Status Legend

- `Not started`: no implementation work has been done.
- `Ready`: can begin with current tools/materials.
- `Blocked`: depends on missing software, credentials, data, or user decision.
- `In progress`: actively being implemented.
- `Complete`: implemented and verified.
