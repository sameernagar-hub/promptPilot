# Phase 14: Evaluation, Privacy, and Production Readiness

## Goal

Make the profile and refinement system trustworthy enough for real user data.

## Status

Not started.

## Evaluation Coverage

```txt
trait detection accuracy
domain detection and confirmation
clarifying question quality
refined prompt completeness
platform-specific prompt fit
profile Q&A grounding
redaction behavior
deletion and reprocessing behavior
```

## Production Features

- Authentication.
- User-owned profiles.
- Prompt and import history.
- Prompt versioning.
- Feedback and ratings.
- Rate limits.
- Model usage and cost tracking.
- Audit logs for model runs and imports.
- Export to Markdown, PDF, and JSON.

## Security and Safety

- PII handling rules.
- Secret redaction.
- Sensitive-domain warnings.
- Medical, legal, financial, repair, and safety boundaries where appropriate.
- Prompt injection checks for imported or retrieved external content.

## Planned Work

- Add or extend the evaluation suite.
- Add tests for privacy-critical behaviors.
- Define auth and ownership boundaries before real chat storage.
- Add export and delete flows for profile data.
- Add audit logs for model runs and imports.

## Verification

- [ ] Evaluation suite runs locally.
- [ ] Privacy-critical behaviors have tests.
- [ ] Auth and ownership are explicit before storing real user chat history.
- [ ] Users can export and delete their profile data.
- [ ] Audit logs exist for imports and model runs.
