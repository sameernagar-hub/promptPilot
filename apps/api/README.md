# PromptPilot API

FastAPI service for the PromptPilot prompt engine.

Local API environment values:

- `APP_ENV=development`
- `DATABASE_URL=postgresql://prompt_engine:prompt_engine@localhost:5432/prompt_engine`
- `LLM_PROVIDER=ollama`
- `OLLAMA_BASE_URL=http://localhost:11434`
- `DEFAULT_MODEL=ollama/llama3.1:8b`
- `ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`

Production must set `APP_ENV=production`, a managed `DATABASE_URL`, a hosted `LLM_PROVIDER`, and the final production web origin in `ALLOWED_ORIGINS`. Production startup fails fast if local database, local Ollama, or localhost CORS values are used.

Run locally from the repository root:

```powershell
uv --directory apps/api run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Phase 3 endpoints:

- `GET /health`
- `POST /sessions`
- `GET /sessions/{session_id}`
- `POST /sessions/{session_id}/end`
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
- `GET /profile/insights`
- `POST /profile/questions`
- `PATCH /profile/observations/{observation_id}`
- `DELETE /profile/observations/{observation_id}`
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

Phase 11 clarification-first refinement:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/sessions/{session_id}/run-pipeline `
  -ContentType 'application/json' `
  -Body '{"mode":"refinement","settings":{"length":"medium","skill_level":"practical","tone":"friendly","format":"guide","risk":"normal","sources":"none"},"answers":[]}'
```

- `run-pipeline` supports `mode: "refinement" | "quick"`.
- Refinement mode returns clarifying questions before generating prompts when required context or domain confirmation is open.
- Clarifying questions store answered, skipped, and revised state.
- Skipped required context is carried into prompt assumptions.
- Prompt revisions are stored in `prompt_revisions`.
- Prompt explanations reference settings, answers/skips, assumptions, and profile traits.

Phase 12 advanced controls and platform output:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/sessions/{session_id}/run-pipeline `
  -ContentType 'application/json' `
  -Body '{"mode":"quick","settings":{"target_platform":"codex","detail_level":"balanced","formality":"neutral","temperature":"precise","reasoning_style":"step_by_step","source_strictness":"official_only","interaction_mode":"agentic","length":"medium","skill_level":"practical","tone":"technical","format":"plan","risk":"normal","sources":"official_docs"}}'
```

- `PromptSettings` supports target platform, detail level, formality, temperature preference, reasoning style, source strictness, and interaction mode.
- Prompt output is shaped for Codex, Claude, ChatGPT, Gemini, Cursor, and generic assistants.
- `run-pipeline` stores the selected platform preference snapshot in `platform_preferences` for the local prompting profile.
- `GET /profile` returns platform preferences so the frontend can seed fresh workspace settings.
- Prompt scores include `platform_fit`.

Phase 13 profile Q&A and dashboard:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/profile/insights
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/profile/questions `
  -ContentType 'application/json' `
  -Body '{"question":"How should I prompt Codex better?"}'
```

- `GET /profile/insights` returns common missing details, preferences, frequent domains, platform advice, and recent prompt revisions.
- `POST /profile/questions` answers from stored traits, signals, sessions, imports, and revisions with evidence references.
- `PATCH /profile/observations/{observation_id}` stores user corrections.
- `DELETE /profile/observations/{observation_id}` hides observations through refresh-safe overrides.
- `GET /profile/export?format=markdown|json` exports derived profile data.
- `DELETE /profile/data` clears derived profile traits, signals, platform preferences, and observation overrides while preserving source sessions/imports.
- `ALLOWED_ORIGINS` configures CORS for the single local frontend port and the final hosted frontend origin.

Phase 14 session onboarding, guardrails, live evaluation, privacy, and audit behavior:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/sessions `
  -ContentType 'application/json' `
  -Body '{"raw_input":"My React app saves data but the UI stays stale","display_name":"Nagar","primary_ai_platform":"codex","rules_accepted":true,"settings":{"target_platform":"codex"}}'
```

- `POST /sessions` now requires `display_name`, `primary_ai_platform`, and `rules_accepted: true`.
- Supported primary AI platforms are ChatGPT, Claude, Grok, Perplexity, Gemini, Copilot, Cursor, Codex, and Other.
- `problem_sessions` stores the session profile, rules acceptance, session metadata, and `ended_at`.
- `POST /sessions/{session_id}/end` marks a session as ended.
- `GET /sessions/{session_id}/export?format=markdown|json` exports session request, questions, prompts, scores, and audit events.
- `DELETE /sessions/{session_id}/data` removes session-scoped questions, prompts, scores, revisions, saved prompts, embeddings, and audit events, then records a non-sensitive deletion completion event.
- `GET /sessions/{session_id}/audit-logs` returns session audit events.
- `run-pipeline` returns Phase 14 scoring dimensions: input-to-contract improvement, contract completeness, assumption handling, domain accuracy, clarification value, platform fit, platform-fit granularity, backend value exposure, safety/privacy integrity, and user actionability.
- Prompt variant responses include modification audit trails, skipped-question assumption notes, platform-fit breakdowns, matched rules, trait alignment, optimization paths, recommended actions, and scorer metadata.
- Prompt metadata is stored on prompt variants and scorer metadata is stored on prompt scores.
- Local Ollama `llama3.1:8b` scoring is wired into the live scorer; model scores are validated and blended with deterministic scores when available.
- Deterministic scoring remains the stable fallback and records why fallback was used.
- Deterministic guardrails block clear misuse requests and return a short safe redirect.
- Import create/reprocess/delete, model-run previews, scorer runs, session lifecycle events, and profile reset are audit logged.
