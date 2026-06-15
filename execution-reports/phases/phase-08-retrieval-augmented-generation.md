# Phase 8: Retrieval-Augmented Prompt Generation

## Goal

Make generation use the prompt knowledge base.

## Status

Not started.

## Prerequisites

- Prompt knowledge base exists.
- Embedding storage exists.
- Retrieval interface exists.

## Planned Pipeline

```txt
user problem
-> classify problem
-> search similar prompt patterns
-> extract reusable structures
-> synthesize new prompt variants
-> apply tuner settings
-> score and recommend
```

## Safety Rule

Do not directly copy retrieved prompts unless licensing explicitly allows it. Prefer pattern extraction and synthesis.

## Verification

- [ ] Similar prompt patterns can be retrieved.
- [ ] Generated variants are synthesized, not copied.
- [ ] License metadata is preserved.
- [ ] Retrieved context cannot override safety rules or user settings.
