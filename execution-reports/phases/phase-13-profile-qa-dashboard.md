# Phase 13: Profile Q&A and UX Dashboard

## Goal

Let users ask questions about their prompting behavior and receive grounded, useful answers.

## Status

Not started.

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

- Add profile Q&A API.
- Add profile dashboard UI.
- Add evidence references to profile answers.
- Add correction and deletion flows for profile observations.
- Add empty-state guidance for users with little data.

## Verification

- [ ] Profile Q&A can answer from stored traits.
- [ ] Answers include evidence references or confidence language.
- [ ] Empty-state guidance appears before enough data exists.
- [ ] Users can correct or delete profile observations.
- [ ] Dashboard layout is verified on mobile and desktop.
