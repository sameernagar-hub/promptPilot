# Phase 10: Open Domain Detection and Confirmation

## Goal

Replace the fixed starter-domain classifier with open domain detection and explicit user confirmation.

## Status

Complete.

## Classification Shape

```txt
primary_domain
subdomain
intent
risk_level
confidence
evidence
alternative_domains
needs_domain_confirmation
confirmed_domain
domain_source: detected | user_confirmed | user_corrected
```

## UX Flow

```txt
detect domain
-> ask "I think this is about X. Is that right?"
-> if yes, continue
-> if no, let user provide or select the correct domain
-> generate domain-aware clarifying questions
```

## Planned Work

- [x] Extend classification schemas and persistence.
- [x] Keep the existing deterministic classifier as a fallback.
- [x] Add an open-domain classifier service that can return alternatives and evidence.
- [x] Add domain confirmation and correction APIs.
- [x] Update prompt generation to use confirmed domains.
- [x] Add UI for confirm, correct, and continue.
- [x] Correct the main workspace UX so the recommended prompt is primary and alternatives are secondary.
- [x] Add import upload support.
- [x] Add first-pass workspace themes.

## Implementation Notes

- `ClassificationResponse` now includes:
  - `primary_domain`
  - `subdomain`
  - `evidence`
  - `alternative_domains`
  - `needs_domain_confirmation`
  - `confirmed_domain`
  - `domain_source`
- The deterministic classifier now supports broader open domains, including:
  - bicycle repair
  - automotive repair
  - home repair
  - software engineering
  - writing and communication
  - learning and research
  - business strategy
  - health and wellness
  - legal or financial
  - creative media
- Added `POST /sessions/{session_id}/domain-confirmation`.
- Domain confirmations are stored in `domain_confirmations`.
- Confirmed or corrected domains update the session classification and persist across pipeline reruns.
- Prompt generation now starts with a `recommended_prompt` strategy and uses a domain-specific expert role.
- User answers are included in the recommended prompt under known details.
- The workspace now:
  - focuses on a single recommended prompt
  - hides advanced preferences behind a button
  - shows domain confirmation/correction
  - puts prompt alternatives behind a toggle
  - displays the full recommended prompt instead of clipping it
  - includes three themes
- `/profile/imports` now has an upload button for `.txt`, `.md`, `.markdown`, and `.json` files.

## Verification

- [x] Prompts outside the original four MVP domains can be classified.
- [x] Ambiguous or low-confidence domains trigger confirmation.
- [x] User-corrected domains are stored.
- [x] Confirmed domains drive clarifying questions and generated prompts.
- [x] Profile analysis can identify recurring user domains through stored session classifications.

Verification commands and checks:

- `uv run python -m compileall app`
- SQLAlchemy mapper configuration registered 20 ORM tables.
- FastAPI `TestClient` Phase 10 smoke:
  - `I need my bike fixed` classified as `bicycle_repair`
  - classification requested domain confirmation
  - recommended prompt used a mechanical engineer / bicycle repair specialist role
  - domain confirmation stored `user_confirmed`
  - rerun preserved the confirmed domain
  - answered bike details appeared in the recommended prompt
  - user-corrected domain stored `user_corrected`
- `uv --directory apps/api run python main.py`
- `pnpm.cmd --dir apps/web lint`
- `pnpm.cmd --dir apps/web build`
- In-app Browser was unavailable; Microsoft Edge Playwright fallback verified:
  - guided workspace load
  - bike prompt generation
  - domain confirmation
  - clarifying answers
  - full recommended prompt detail injection
  - alternatives toggle
  - theme switcher
  - import upload button
