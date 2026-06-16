# Phase 9: Chat History Import and Integration Foundation

## Goal

Let PromptPilot study previous AI chats safely, starting with user-provided imports before direct account integrations.

## Status

Not started.

## Import Paths

- Paste raw chat.
- Upload Markdown.
- Upload JSON export.
- Upload text transcript.
- Manual conversation entry.

## Platform Adapter Contract

```txt
platform
source_type
external_conversation_id
conversation_title
message_role
message_text
message_timestamp
metadata
consent_status
redaction_status
```

## Target Future Platforms

- Codex
- Claude
- ChatGPT
- Gemini
- Cursor
- Windsurf
- Custom MCP tools or local transcript folders

## Privacy Rules

- Do not require direct account integrations for the first version.
- Let the user review imported text before analysis.
- Redact obvious secrets, API keys, tokens, emails, and phone numbers.
- Provide delete and reprocess controls.
- Keep provider tokens server-side only.

## Planned Work

- Add import models and API endpoints.
- Add a normalization service for imported conversations and messages.
- Add a redaction service for common sensitive patterns.
- Add an import review UI.
- Feed normalized imports into trait detection.

## Verification

- [ ] Imported conversations normalize into a common schema.
- [ ] Imported content can produce prompting trait observations.
- [ ] Redaction status is visible.
- [ ] Deleting an import removes or stales derived profile observations.
- [ ] No direct provider credentials are required for the first version.
