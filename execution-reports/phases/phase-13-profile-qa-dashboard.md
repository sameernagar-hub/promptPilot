# Phase 13: Profile Q&A and UX Dashboard

## Goal

Let users ask questions about their prompting behavior and receive grounded, useful answers.

## Status

Complete.

## Example User Questions

```txt
What do I usually forget to include?
Why do my prompts get vague answers?
How should I prompt Codex better?
What tone do I usually prefer?
Which domains do I ask about most?
How can I make my research prompts stronger?
```

## Dashboard Sections

- Prompting profile summary.
- Trait cards with confidence and examples.
- Common missing details.
- Preferred tone, format, and detail level.
- Frequent domains and task types.
- Platform-specific advice.
- Recent prompt revisions and improvement history.

## Grounding Rules

- Answers should cite profile observations or imported conversation evidence.
- If there is not enough evidence, say so and ask for more examples.
- The dashboard should help the user improve without sounding judgmental.
- Users should be able to correct or delete profile observations.

## Planned Work

- [x] Add profile Q&A API.
- [x] Add profile dashboard UI.
- [x] Add evidence references to profile answers.
- [x] Add correction and deletion flows for profile observations.
- [x] Add empty-state guidance for users with little data.

## Implementation Notes

- Added `GET /profile/insights` for dashboard guidance sections.
- Added `POST /profile/questions` for grounded profile Q&A.
- Added `PATCH /profile/observations/{observation_id}` for user corrections.
- Added `DELETE /profile/observations/{observation_id}` for hiding observations.
- Added `profile_observation_overrides` so user corrections and hidden observations survive profile refreshes.
- Expanded `/profile` into a responsive Q&A and insight dashboard.
- Added environment-driven API CORS through `ALLOWED_ORIGINS`.

## Verification

- [x] Profile Q&A can answer from stored traits.
- [x] Answers include evidence references or confidence language.
- [x] Empty-state guidance appears before enough data exists.
- [x] Users can correct or delete profile observations.
- [x] Dashboard layout is verified on mobile and desktop.
- [x] `uv --directory apps/api run python -m compileall app` passes.
- [x] `pnpm.cmd --dir apps/web lint` passes.
- [x] `pnpm.cmd --dir apps/web build` passes.
- [x] FastAPI smoke test passed for health, session creation, pipeline, profile refresh, insights, Q&A, correction, and hide flows.
- [x] Local production Next.js profile page works against the API from `http://127.0.0.1:3001`.
