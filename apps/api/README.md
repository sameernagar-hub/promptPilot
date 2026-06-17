# PromptPilot API

FastAPI service for the PromptPilot prompt engine.

Run locally from the repository root:

```powershell
uv --directory apps/api run uvicorn app.main:app --reload
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Phase 3 endpoints:

- `GET /health`
- `POST /sessions`
- `GET /sessions/{session_id}`
- `POST /sessions/{session_id}/classify`
- `POST /sessions/{session_id}/domain-confirmation`
- `POST /sessions/{session_id}/questions`
- `POST /sessions/{session_id}/answers`
- `POST /sessions/{session_id}/generate-prompts`
- `POST /sessions/{session_id}/score-prompts`
- `POST /sessions/{session_id}/run-pipeline`
- `POST /sessions/{session_id}/run-prompt`
- `POST /prompts/{prompt_id}/save`
- `GET /saved-prompts`
- `GET /profile`
- `POST /profile/refresh`
- `POST /imports`
- `GET /imports`
- `GET /imports/{import_id}`
- `POST /imports/{import_id}/reprocess`
- `DELETE /imports/{import_id}`

Phase 4 persistence:

- The API uses SQLAlchemy with local Postgres.
- Tables are bootstrapped locally with `Base.metadata.create_all()`.
- pgvector is enabled before table creation.
- `prompt_embeddings.embedding` uses pgvector `vector(1536)`.
- Formal migration tooling is deferred until schema churn justifies it.

Phase 5 pipeline endpoint:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/sessions/{session_id}/run-pipeline `
  -ContentType 'application/json' `
  -Body '{"settings":{"length":"medium","skill_level":"practical","tone":"friendly","format":"guide","risk":"normal","sources":"none"}}'
```

The pipeline runs locally without an external LLM. It classifies, generates clarifying questions, merges supplied answers/settings, creates 3 prompt variants, scores them, and returns a deterministic recommendation.

Phase 7 profile endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/profile
Invoke-RestMethod -Method Post http://127.0.0.1:8000/profile/refresh
```

The profile foundation stores prompting traits separately from prompt variants. The active analyzer version, `trait_detector_v1`, derives evidence-backed observations from local sessions and imported user messages.

Phase 8 trait detection:

- `prompting_trait_signals` stores per-example signals beneath aggregate observations.
- `trait_detector_v1` normalizes local sessions and imported user messages.
- Profile responses include evidence level, signal count, and representative signal explanations for each trait.

Phase 9 chat imports:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/imports `
  -ContentType 'application/json' `
  -Body '{"platform":"codex","source_type":"paste","title":"Example","raw_text":"User: Build a detailed prompt\nAssistant: Sure"}'
```

- `chat_import_normalizer_v1` normalizes pasted transcripts and JSON-style exports into imported conversations and messages.
- Import previews return redacted text for obvious secrets, OpenAI-style keys, bearer tokens, emails, and phone numbers.
- `POST /imports/{import_id}/reprocess` refreshes the profile from existing normalized messages.
- `DELETE /imports/{import_id}` removes the import and derived trait signals, then refreshes the profile.

Phase 10 open-domain confirmation:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/sessions/{session_id}/domain-confirmation `
  -ContentType 'application/json' `
  -Body '{"confirmed_domain":"bicycle_repair","accepted":true}'
```

- Classification responses include subdomain, evidence, alternatives, confirmation state, confirmed domain, and domain source.
- Confirmed and corrected domains are stored in `domain_confirmations`.
- The prompt engine preserves confirmed domains across reruns.
- The recommended prompt uses the confirmed domain and injects answered clarifying details.
