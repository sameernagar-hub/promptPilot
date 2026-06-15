# Raw Materials Inventory

This file lists the project ingredients from `EXECUTION_LOG.md` so implementation can proceed without guessing.

## Product Materials

- Product name: PromptPilot
- Product purpose: dynamic prompt intelligence platform.
- Primary promise: "Tell us your problem. We will build the best AI request for it."
- MVP goal: turn messy problems into classified, clarified, tunable, scored prompt variants.

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

## External Prompt Source Rules

- Only ingest open-source, user-submitted, explicitly licensed, public domain, permissively licensed, or project-created prompt examples.
- Do not scrape paid or private prompt libraries.
- Always track source, URL, license, author, allowed usage, domain, intent, prompt type, and quality score.
