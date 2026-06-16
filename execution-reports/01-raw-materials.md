# Raw Materials Inventory

This file lists the project ingredients from `EXECUTION_LOG.md` so implementation can proceed without guessing.

## Product Materials

- Product name: PromptPilot
- Product purpose: prompting experience intelligence platform.
- Primary promise: "Understand how you prompt. Then help you ask every AI system better."
- Completed MVP goal: turn messy problems into classified, clarified, tunable, scored prompt variants.
- Revised roadmap goal: build prompting profiles, study imported chat history, confirm domains, ask clarifying questions before recommendation, and generate platform-aware refined prompts.

## MVP User Capabilities

- Enter a messy problem.
- Detect domain and intent.
- Answer clarifying questions.
- Tune prompt settings.
- Generate at least 3 prompt variants.
- Compare scores and explanations.
- Copy or run selected prompts.
- Save prompts to a personal library.

## Initial MVP Domains

- Car/home troubleshooting
- Software/project building
- Writing/business communication
- Learning/research

## Revised Product Capabilities

- Detect prompting traits from sessions and imported AI chats.
- Build a user prompting profile with evidence and confidence.
- Detect open-ended domains and ask the user to confirm or correct them.
- Ask clarifying questions before recommending a refined prompt.
- Let users tune tone, formality, detail, temperature, risk posture, source strictness, output format, and target platform.
- Generate detailed prompts for Codex, Claude, ChatGPT, Gemini, Cursor, or a generic AI platform.
- Let users ask questions about their own prompting patterns.

## Recommended Frontend Materials

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- lucide-react
- class-variance-authority
- clsx
- tailwind-merge

## Recommended Backend Materials

- FastAPI
- Python 3.10+
- Pydantic
- SQLAlchemy
- Uvicorn
- psycopg binary package
- pgvector Python package
- python-dotenv
- LiteLLM
- DSPy

## Database and Infrastructure Materials

- Postgres
- pgvector
- Docker Compose
- Optional later:
  - Langfuse
  - LiteLLM proxy
  - Qdrant or Chroma

## AI and Evaluation Materials

- Ollama
- Initial model: `llama3.1:8b`
- LiteLLM provider abstraction
- DSPy signatures and optimizers
- promptfoo evaluation config
- Langfuse tracing and prompt management

## Future Workflow Materials

- CrewAI or AutoGen
- MCP integrations
- Langflow, Dify, or Flowise as optional visual workflow builders

## Future Integration Materials

- User-provided chat imports.
- Markdown transcript parser.
- JSON export parser.
- Text transcript parser.
- Redaction rules for API keys, tokens, emails, phone numbers, and obvious secrets.
- Adapter contract for Codex, Claude, ChatGPT, Gemini, Cursor, Windsurf, MCP tools, and local transcript folders.

## Planned Root Structure

```txt
promptPilot/
  apps/
    web/
    api/
  packages/
    shared/
  infra/
    docker-compose.yml
  docs/
    architecture.md
    product-spec.md
    prompt-engine.md
  scripts/
  datasets/
    prompt-sources/
  evals/
    promptfoo/
  .env.example
  README.md
  EXECUTION_LOG.md
```

## Backend Modules To Create Later

```txt
apps/api/
  app/
    main.py
    config.py
    db.py
    models.py
    schemas.py
    services/
      classifier.py
      question_generator.py
      prompt_generator.py
      prompt_scorer.py
      llm_client.py
    routers/
      sessions.py
      prompts.py
      health.py
```

## Initial API Surface

- `GET /health`
- `POST /sessions`
- `GET /sessions/{session_id}`
- `POST /sessions/{session_id}/classify`
- `POST /sessions/{session_id}/questions`
- `POST /sessions/{session_id}/answers`
- `POST /sessions/{session_id}/generate-prompts`
- `POST /sessions/{session_id}/score-prompts`
- `POST /sessions/{session_id}/run-prompt`
- `POST /prompts/{prompt_id}/save`
- `GET /saved-prompts`

## Core Database Tables

- `users`
- `problem_sessions`
- `clarifying_questions`
- `prompt_variants`
- `prompt_scores`
- `saved_prompts`
- `prompt_sources`
- `prompt_embeddings`
- `domain_packs`

## Planned Profile and Import Tables

- `user_prompt_profiles`
- `prompting_traits`
- `trait_observations`
- `conversation_imports`
- `imported_conversations`
- `imported_messages`
- `prompt_revisions`
- `domain_confirmations`
- `platform_preferences`
- `integration_connections`

## Planned Profile API Surface

- `GET /profile`
- `POST /profile/refresh`
- `GET /profile/traits`
- `POST /profile/questions`
- `DELETE /profile/observations/{observation_id}`
- `POST /imports`
- `GET /imports`
- `GET /imports/{import_id}`
- `DELETE /imports/{import_id}`
- `POST /sessions/{session_id}/confirm-domain`
- `POST /sessions/{session_id}/refine`

## Prompt Strategies

- `diagnostic`
- `beginner_step_by_step`
- `expert_consultant`
- `safety_first`
- `comparison`
- `questions_first`

## Prompt Tuning Settings

- `length`: short, medium, deep
- `skill_level`: beginner, practical, expert
- `tone`: direct, friendly, technical
- `format`: checklist, guide, table, conversation, plan
- `risk`: safe_only, normal, advanced
- `sources`: none, web, official_docs

## Planned Advanced Prompt Controls

- `target_platform`: codex, claude, chatgpt, gemini, cursor, generic
- `detail_level`: concise, balanced, exhaustive
- `formality`: casual, neutral, formal
- `temperature`: precise, balanced, creative
- `reasoning_style`: direct_answer, step_by_step, ask_first, explore_options
- `source_strictness`: none, cite_when_needed, official_only, evidence_first
- `interaction_mode`: one_shot, iterative, agentic

## Prompting Trait Dimensions

- context_depth
- goal_clarity
- constraint_specificity
- domain_precision
- format_preference
- tone_preference
- formality_preference
- iteration_style
- risk_awareness
- source_expectation
- technical_depth
- missing_context_patterns

## Scoring Dimensions

- clarity
- specificity
- safety
- actionability
- domain_fit
- beginner_friendliness
- expected_answer_quality

## Frontend Screens

- `/`: main workspace
- `/sessions/[id]`: session detail
- `/compare/[id]`: prompt comparison view
- `/library`: saved prompt library
- `/settings`: model and user settings
- `/profile`: prompting profile dashboard
- `/profile/imports`: chat import review
- `/profile/questions`: profile Q&A

## Frontend Components

- `ProblemInput`
- `DomainBadge`
- `ClarifyingQuestions`
- `PromptTuner`
- `PromptCard`
- `PromptScoreBars`
- `PromptCompareGrid`
- `AgentTimeline`
- `RunPromptPanel`
- `SavedPromptList`
- `ModelSelector`
- `ProfileSummary`
- `TraitCard`
- `ChatImportPanel`
- `DomainConfirmation`
- `RefinementQuestions`
- `PlatformSelector`

## Icons

- `Copy`
- `Play`
- `Save`
- `RefreshCw`
- `SlidersHorizontal`
- `GitCompare`
- `Sparkles`
- `ShieldCheck`

## Evaluation Scenarios

- Car clicks but will not start
- Sink leaking under cabinet
- React app state bug
- Difficult email to manager
- Research topic summary
- Legal letter explanation
- Workout plan request
- Insurance plan comparison

## Revised Evaluation Targets

- Trait detection accuracy
- Domain detection and confirmation
- Clarifying question quality
- Refined prompt completeness
- Platform-specific prompt fit
- Profile Q&A grounding
- Redaction behavior
- Deletion and reprocessing behavior

## Deferred External Prompt Source Rules

- Only ingest open-source, user-submitted, explicitly licensed, public domain, permissively licensed, or project-created prompt examples.
- Do not scrape paid or private prompt libraries.
- Always track source, URL, license, author, allowed usage, domain, intent, prompt type, and quality score.
- External prompt source ingestion is deferred until the profile, import, domain confirmation, and refinement phases are stable.
