# Phase 9: Chat History Import and Integration Foundation

## Goal

Let PromptPilot study previous AI chats safely, starting with user-provided imports before direct account integrations.

## Status

Complete.

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

- [x] Add import models and API endpoints.
- [x] Add a normalization service for imported conversations and messages.
- [x] Add a redaction service for common sensitive patterns.
- [x] Add an import review UI.
- [x] Feed normalized imports into trait detection.

## Implementation Notes

- Reused the Phase 7 import tables:
  - `conversation_imports`
  - `imported_conversations`
  - `imported_messages`
- Added `chat_import_normalizer_v1` in `apps/api/app/services/import_normalizer.py`.
- Added parsing support for:
  - pasted role-prefixed transcripts
  - plain text transcripts
  - message-list JSON
  - generic conversation JSON
  - ChatGPT-style mapping JSON
- Added redaction for:
  - obvious secret assignments
  - OpenAI-style `sk-...` keys
  - bearer tokens
  - emails
  - phone numbers
- Added `/imports` routes:
  - `POST /imports`
  - `GET /imports`
  - `GET /imports/{import_id}`
  - `POST /imports/{import_id}/reprocess`
  - `DELETE /imports/{import_id}`
- Added `/profile/imports` in the frontend.
- The import review UI supports:
  - platform selection
  - source type selection
  - transcript entry
  - redaction status
  - import ledger
  - redacted message preview
  - reprocess
  - delete
- Import creation and reprocessing refresh the prompting profile.
- Import deletion removes derived trait signals before deleting imported messages, then refreshes the profile.

## Verification

- [x] Imported conversations normalize into a common schema.
- [x] Imported content can produce prompting trait observations.
- [x] Redaction status is visible.
- [x] Deleting an import removes or stales derived profile observations.
- [x] No direct provider credentials are required for the first version.

Verification commands and checks:

- `uv run python -m compileall app`
- SQLAlchemy mapper configuration registered 20 ORM tables.
- FastAPI `TestClient` smoke test:
  - created a Codex import from a pasted transcript
  - verified 1 normalized conversation and 3 messages
  - verified fake key and email were redacted in preview text
  - fetched the saved import
  - refreshed the profile and confirmed imported user messages contributed signals
  - reprocessed the import
  - deleted the import
  - confirmed the import returned `404` after deletion
- `uv --directory apps/api run python main.py`
- `pnpm.cmd --dir apps/web lint`
- `pnpm.cmd --dir apps/web build`
- Microsoft Edge Playwright fallback verified `/profile/imports` because the in-app Browser connector was unavailable.
