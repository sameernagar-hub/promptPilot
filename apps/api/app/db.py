from collections.abc import Iterable

from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.config import get_settings
from app.models import (
    AuditLog,
    Base,
    ClarifyingQuestion,
    CoachingObservation,
    DomainConfirmation,
    PlatformPreference,
    ProblemSession,
    PromptEmbedding,
    PromptSource,
    PromptingTraitSignal,
    PromptRevision,
    PromptScore,
    PromptVariant,
    SavedPrompt,
    TraitObservation,
    UserPromptProfile,
    utc_now,
)


def _sqlalchemy_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


engine = create_engine(
    _sqlalchemy_database_url(get_settings().database_url),
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_database() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=connection)
        connection.execute(
            text(
                "ALTER TABLE clarifying_questions "
                "ADD COLUMN IF NOT EXISTS answer_state VARCHAR(40) "
                "DEFAULT 'unanswered' NOT NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE clarifying_questions "
                "ADD COLUMN IF NOT EXISTS revision_count INTEGER "
                "DEFAULT 0 NOT NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE problem_sessions "
                "ADD COLUMN IF NOT EXISTS display_name VARCHAR(120)"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE problem_sessions "
                "ADD COLUMN IF NOT EXISTS primary_ai_platform VARCHAR(80)"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE problem_sessions "
                "ADD COLUMN IF NOT EXISTS rules_accepted BOOLEAN "
                "DEFAULT FALSE NOT NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE problem_sessions "
                "ADD COLUMN IF NOT EXISTS metadata JSONB "
                "DEFAULT '{}'::jsonb NOT NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE problem_sessions "
                "ADD COLUMN IF NOT EXISTS ended_at TIMESTAMP WITH TIME ZONE"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE prompt_variants "
                "ADD COLUMN IF NOT EXISTS metadata JSONB "
                "DEFAULT '{}'::jsonb NOT NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE prompt_scores "
                "ADD COLUMN IF NOT EXISTS metadata JSONB "
                "DEFAULT '{}'::jsonb NOT NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE prompt_sources "
                "ADD COLUMN IF NOT EXISTS author VARCHAR(200)"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE prompt_sources "
                "ADD COLUMN IF NOT EXISTS allowed_usage VARCHAR(120) "
                "DEFAULT 'pattern_synthesis_only' NOT NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE prompt_sources "
                "ADD COLUMN IF NOT EXISTS prompt_type VARCHAR(120)"
            )
        )


def _session_load_options():
    return (
        selectinload(ProblemSession.question_rows),
        selectinload(ProblemSession.prompts),
    )


def _prompt_load_options():
    return (
        selectinload(PromptVariant.score_rows),
        selectinload(PromptVariant.saved_prompts),
    )


class DatabaseStore:
    def create_session(
        self,
        raw_input: str,
        user_settings: dict,
        display_name: str | None = None,
        primary_ai_platform: str | None = None,
        rules_accepted: bool = False,
        session_metadata: dict | None = None,
    ) -> ProblemSession:
        with SessionLocal() as database:
            session = ProblemSession(
                raw_input=raw_input,
                user_settings=user_settings,
                display_name=display_name,
                primary_ai_platform=primary_ai_platform,
                rules_accepted=rules_accepted,
                session_metadata=session_metadata or {},
            )
            database.add(session)
            database.flush()
            database.add(
                AuditLog(
                    session_id=session.id,
                    entity_type="problem_session",
                    entity_id=session.id,
                    event_type="session_started",
                    event_metadata={
                        "display_name": display_name,
                        "primary_ai_platform": primary_ai_platform,
                        "rules_accepted": rules_accepted,
                    },
                )
            )
            database.commit()
            session_id = session.id
        return self.get_session(session_id) or session

    def get_session(self, session_id: str) -> ProblemSession | None:
        with SessionLocal() as database:
            statement = (
                select(ProblemSession)
                .options(*_session_load_options())
                .where(ProblemSession.id == session_id)
            )
            return database.scalar(statement)

    def upsert_session(self, session: ProblemSession) -> ProblemSession:
        with SessionLocal() as database:
            db_session = _get_session_for_update(database, session.id)
            _copy_session_scalars(db_session, session)
            db_session.touch(session.status)
            database.commit()
        return self.get_session(session.id) or session

    def replace_session_questions(
        self,
        session: ProblemSession,
        questions: Iterable,
    ) -> ProblemSession:
        with SessionLocal() as database:
            db_session = _get_session_for_update(database, session.id)
            previous_answers = {
                question.question_key: {
                    "answer": question.answer,
                    "answer_state": question.answer_state,
                    "revision_count": question.revision_count,
                }
                for question in db_session.question_rows
            }
            database.execute(
                delete(ClarifyingQuestion).where(
                    ClarifyingQuestion.session_id == db_session.id
                )
            )
            database.flush()
            for position, question in enumerate(questions):
                previous = previous_answers.get(question.id, {})
                db_session.question_rows.append(
                    ClarifyingQuestion(
                        question_key=question.id,
                        question=question.question,
                        reason=question.reason,
                        required=question.required,
                        answer=previous.get("answer"),
                        answer_state=previous.get("answer_state") or "unanswered",
                        revision_count=previous.get("revision_count") or 0,
                        position=position,
                    )
                )
            db_session.touch("questions_ready")
            database.commit()
        return self.get_session(session.id) or session

    def record_answers(
        self,
        session: ProblemSession,
        answers: Iterable,
    ) -> ProblemSession:
        with SessionLocal() as database:
            db_session = _get_session_for_update(database, session.id)
            existing = {question.question_key: question for question in db_session.question_rows}
            next_position = len(existing)
            for answer in answers:
                question = existing.get(answer.question_id)
                if question is None:
                    question = ClarifyingQuestion(
                        question_key=answer.question_id,
                        question=answer.question_id,
                        reason="User-provided answer without a generated question.",
                        required=False,
                        position=next_position,
                    )
                    next_position += 1
                    db_session.question_rows.append(question)
                    existing[answer.question_id] = question
                next_state = answer.state or ("answered" if answer.answer else "unanswered")
                next_answer = answer.answer.strip() if answer.answer else None
                if next_state == "skipped":
                    next_answer = None
                elif next_state == "answered" and not next_answer:
                    next_state = "unanswered"
                changed = (
                    question.answer_state != next_state
                    or (question.answer or None) != next_answer
                )
                if changed and question.answer_state != "unanswered":
                    question.revision_count += 1
                question.answer_state = next_state
                question.answer = next_answer
            db_session.touch("answers_recorded")
            database.commit()
        return self.get_session(session.id) or session

    def replace_session_prompts(
        self,
        session: ProblemSession,
        prompts: list[PromptVariant],
    ) -> list[PromptVariant]:
        with SessionLocal() as database:
            db_session = _get_session_for_update(database, session.id)
            for existing_prompt in db_session.prompts:
                existing_prompt.is_active = False
            for prompt in prompts:
                prompt.session_id = session.id
                prompt.is_active = True
                database.add(prompt)
            db_session.touch("prompts_generated")
            database.add(
                AuditLog(
                    session_id=session.id,
                    entity_type="problem_session",
                    entity_id=session.id,
                    event_type="prompts_generated",
                    event_metadata={"prompt_count": len(prompts)},
                )
            )
            database.commit()
            for prompt in prompts:
                database.refresh(prompt)
            return prompts

    def get_session_prompts(self, session: ProblemSession) -> list[PromptVariant]:
        with SessionLocal() as database:
            statement = (
                select(PromptVariant)
                .options(*_prompt_load_options())
                .where(
                    PromptVariant.session_id == session.id,
                    PromptVariant.is_active.is_(True),
                )
                .order_by(PromptVariant.created_at)
            )
            return list(database.scalars(statement))

    def get_prompt(self, prompt_id: str | None) -> PromptVariant | None:
        if prompt_id is None:
            return None
        with SessionLocal() as database:
            statement = (
                select(PromptVariant)
                .options(*_prompt_load_options())
                .where(PromptVariant.id == prompt_id)
            )
            return database.scalar(statement)

    def upsert_prompt(self, prompt: PromptVariant) -> PromptVariant:
        with SessionLocal() as database:
            merged_prompt = database.merge(prompt)
            if merged_prompt.score_total is not None:
                scorer_metadata = (merged_prompt.score_metadata or {}).get("scorer_metadata") or {}
                database.add(
                    PromptScore(
                        prompt_variant_id=merged_prompt.id,
                        score_total=merged_prompt.score_total,
                        score_breakdown=merged_prompt.score_breakdown,
                        explanation=merged_prompt.explanation,
                        scorer_version=str(
                            scorer_metadata.get("scorer_version")
                            or scorer_metadata.get("version")
                            or "phase14-deterministic-v1"
                        ),
                        scorer_metadata=scorer_metadata,
                    )
                )
                database.add(
                    AuditLog(
                        session_id=merged_prompt.session_id,
                        entity_type="prompt_variant",
                        entity_id=merged_prompt.id,
                        event_type="prompt_scored",
                        event_metadata={
                            "score_total": merged_prompt.score_total,
                            "score_breakdown": merged_prompt.score_breakdown,
                            "scorer_metadata": scorer_metadata,
                        },
                    )
                )
            database.commit()
            database.refresh(merged_prompt)
            return merged_prompt

    def end_session(self, session_id: str) -> ProblemSession:
        with SessionLocal() as database:
            db_session = _get_session_for_update(database, session_id)
            db_session.status = "ended"
            db_session.ended_at = utc_now()
            db_session.updated_at = utc_now()
            database.add(
                AuditLog(
                    session_id=db_session.id,
                    entity_type="problem_session",
                    entity_id=db_session.id,
                    event_type="session_ended",
                    event_metadata={"ended_at": db_session.ended_at.isoformat()},
                )
            )
            database.commit()
        return self.get_session(session_id) or db_session

    def save_prompt(self, saved_prompt: SavedPrompt) -> SavedPrompt:
        with SessionLocal() as database:
            database.add(saved_prompt)
            database.commit()
            database.refresh(saved_prompt)
            return saved_prompt

    def record_prompt_revision(self, revision: PromptRevision) -> PromptRevision:
        with SessionLocal() as database:
            database.add(revision)
            database.flush()
            database.add(
                AuditLog(
                    session_id=revision.session_id,
                    entity_type="prompt_revision",
                    entity_id=revision.id,
                    event_type="prompt_revision_stored",
                    event_metadata={
                        "revision_type": revision.revision_type,
                        "prompt_variant_id": revision.prompt_variant_id,
                    },
                )
            )
            database.commit()
            database.refresh(revision)
            return revision

    def list_prompt_revisions(self, session_id: str) -> list[PromptRevision]:
        with SessionLocal() as database:
            statement = (
                select(PromptRevision)
                .where(PromptRevision.session_id == session_id)
                .order_by(PromptRevision.created_at.desc())
            )
            return list(database.scalars(statement))

    def upsert_platform_preference(
        self,
        platform: str,
        preference: dict,
        confidence: float = 0.75,
    ) -> PlatformPreference:
        with SessionLocal() as database:
            profile = _ensure_local_profile(database)
            statement = (
                select(PlatformPreference)
                .where(
                    PlatformPreference.profile_id == profile.id,
                    PlatformPreference.platform == platform,
                )
                .order_by(PlatformPreference.updated_at.desc())
            )
            platform_preference = database.scalar(statement)
            if platform_preference is None:
                platform_preference = PlatformPreference(
                    profile_id=profile.id,
                    platform=platform,
                )
                database.add(platform_preference)
            platform_preference.preference = preference
            platform_preference.confidence = confidence
            platform_preference.updated_at = utc_now()
            profile.updated_at = utc_now()
            database.commit()
            database.refresh(platform_preference)
            return platform_preference

    def list_saved_prompts(self) -> list[SavedPrompt]:
        with SessionLocal() as database:
            statement = select(SavedPrompt).order_by(SavedPrompt.created_at.desc())
            return list(database.scalars(statement))

    def create_prompt_source(self, source: PromptSource) -> PromptSource:
        with SessionLocal() as database:
            database.add(source)
            database.commit()
            database.refresh(source)
            return source

    def list_prompt_sources(
        self,
        domain: str | None = None,
        intent: str | None = None,
        limit: int = 20,
    ) -> list[PromptSource]:
        with SessionLocal() as database:
            statement = select(PromptSource)
            if domain:
                statement = statement.where(
                    (PromptSource.domain == domain) | (PromptSource.domain.is_(None))
                )
            if intent:
                statement = statement.where(
                    (PromptSource.intent == intent) | (PromptSource.intent.is_(None))
                )
            statement = statement.order_by(
                PromptSource.quality_score.desc().nullslast(),
                PromptSource.created_at.desc(),
            ).limit(limit)
            return list(database.scalars(statement))

    def confirm_session_domain(
        self,
        session_id: str,
        classification: dict,
        confirmed_domain: str,
        domain_source: str,
        confidence: float,
        evidence: list[dict],
    ) -> ProblemSession:
        with SessionLocal() as database:
            db_session = _get_session_for_update(database, session_id)
            db_session.detected_domain = confirmed_domain
            db_session.detected_intent = classification.get("intent")
            db_session.risk_level = classification.get("risk_level")
            db_session.classification = classification
            db_session.touch("domain_confirmed")
            database.add(
                DomainConfirmation(
                    session_id=db_session.id,
                    detected_domain=classification.get("primary_domain"),
                    confirmed_domain=confirmed_domain,
                    domain_source=domain_source,
                    confidence=confidence,
                    evidence=evidence,
                )
            )
            database.commit()
        return self.get_session(session_id) or db_session

    def record_audit_log(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str | None = None,
        session_id: str | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:
        with SessionLocal() as database:
            row = AuditLog(
                session_id=session_id,
                entity_type=entity_type,
                entity_id=entity_id,
                event_type=event_type,
                event_metadata=metadata or {},
            )
            database.add(row)
            database.commit()
            database.refresh(row)
            return row

    def list_session_audit_logs(self, session_id: str) -> list[AuditLog]:
        with SessionLocal() as database:
            statement = (
                select(AuditLog)
                .where(AuditLog.session_id == session_id)
                .order_by(AuditLog.created_at.desc())
            )
            return list(database.scalars(statement))

    def replace_session_coaching_observations(
        self,
        session_id: str,
        observations: list[CoachingObservation],
    ) -> list[CoachingObservation]:
        with SessionLocal() as database:
            database.execute(
                delete(CoachingObservation).where(
                    CoachingObservation.session_id == session_id
                )
            )
            database.flush()
            for observation in observations:
                observation.session_id = session_id
                database.add(observation)
            database.commit()
            for observation in observations:
                database.refresh(observation)
            return observations

    def list_session_coaching_observations(
        self,
        session_id: str,
    ) -> list[CoachingObservation]:
        with SessionLocal() as database:
            statement = (
                select(CoachingObservation)
                .where(CoachingObservation.session_id == session_id)
                .order_by(CoachingObservation.created_at)
            )
            return list(database.scalars(statement))

    def recent_coaching_session_ids(
        self,
        habit_id: str,
        exclude_session_id: str,
        limit: int = 2,
    ) -> list[str]:
        with SessionLocal() as database:
            statement = (
                select(CoachingObservation.session_id)
                .where(
                    CoachingObservation.habit_id == habit_id,
                    CoachingObservation.session_id != exclude_session_id,
                    CoachingObservation.user_feedback != "rejected",
                )
                .order_by(CoachingObservation.created_at.desc())
                .limit(limit)
            )
            seen: list[str] = []
            for session_id in database.scalars(statement):
                if session_id not in seen:
                    seen.append(session_id)
            return seen

    def update_coaching_feedback(
        self,
        observation_id: str,
        session_id: str,
        feedback: str,
    ) -> CoachingObservation | None:
        with SessionLocal() as database:
            observation = database.scalar(
                select(CoachingObservation).where(
                    CoachingObservation.id == observation_id,
                    CoachingObservation.session_id == session_id,
                )
            )
            if observation is None:
                return None
            observation.user_feedback = feedback
            observation.updated_at = utc_now()
            if observation.prompt_variant_id:
                prompt = database.scalar(
                    select(PromptVariant).where(
                        PromptVariant.id == observation.prompt_variant_id
                    )
                )
                if prompt is not None:
                    metadata = dict(prompt.score_metadata or {})
                    observations = []
                    for item in metadata.get("coaching_observations") or []:
                        if item.get("id") == observation.id:
                            observations.append(
                                {
                                    **item,
                                    "user_feedback": feedback,
                                    "updated_at": observation.updated_at.isoformat(),
                                }
                            )
                        else:
                            observations.append(item)
                    metadata["coaching_observations"] = observations
                    prompt.score_metadata = metadata
            database.commit()
            database.refresh(observation)
            return observation

    def delete_session_data(self, session_id: str) -> dict[str, int]:
        with SessionLocal() as database:
            db_session = database.scalar(
                select(ProblemSession).where(ProblemSession.id == session_id)
            )
            if db_session is None:
                raise ValueError(f"Session not found: {session_id}")
            prompt_ids = [
                prompt_id
                for prompt_id in database.scalars(
                    select(PromptVariant.id).where(PromptVariant.session_id == session_id)
                )
            ]
            counts: dict[str, int] = {}
            if prompt_ids:
                counts["prompt_scores"] = _deleted_count(
                    database.execute(
                        delete(PromptScore).where(PromptScore.prompt_variant_id.in_(prompt_ids))
                    )
                )
                counts["prompt_embeddings"] = _deleted_count(
                    database.execute(
                        delete(PromptEmbedding).where(
                            PromptEmbedding.prompt_variant_id.in_(prompt_ids)
                        )
                    )
                )
            else:
                counts["prompt_scores"] = 0
                counts["prompt_embeddings"] = 0

            counts["saved_prompts"] = _deleted_count(
                database.execute(delete(SavedPrompt).where(SavedPrompt.session_id == session_id))
            )
            counts["prompt_revisions"] = _deleted_count(
                database.execute(
                    delete(PromptRevision).where(PromptRevision.session_id == session_id)
                )
            )
            counts["domain_confirmations"] = _deleted_count(
                database.execute(
                    delete(DomainConfirmation).where(DomainConfirmation.session_id == session_id)
                )
            )
            counts["trait_signals"] = _deleted_count(
                database.execute(
                    delete(PromptingTraitSignal).where(
                        PromptingTraitSignal.session_id == session_id
                    )
                )
            )
            counts["trait_observations"] = _deleted_count(
                database.execute(
                    delete(TraitObservation).where(TraitObservation.session_id == session_id)
                )
            )
            counts["coaching_observations"] = _deleted_count(
                database.execute(
                    delete(CoachingObservation).where(
                        CoachingObservation.session_id == session_id
                    )
                )
            )
            counts["clarifying_questions"] = _deleted_count(
                database.execute(
                    delete(ClarifyingQuestion).where(ClarifyingQuestion.session_id == session_id)
                )
            )
            counts["prompt_variants"] = _deleted_count(
                database.execute(
                    delete(PromptVariant).where(PromptVariant.session_id == session_id)
                )
            )
            counts["session_audit_logs"] = _deleted_count(
                database.execute(delete(AuditLog).where(AuditLog.session_id == session_id))
            )
            database.delete(db_session)
            counts["problem_sessions"] = 1
            database.add(
                AuditLog(
                    session_id=None,
                    entity_type="problem_session",
                    entity_id=session_id,
                    event_type="session_data_deleted",
                    event_metadata={"deleted_counts": counts},
                )
            )
            database.commit()
            return counts


def _get_session_for_update(database: Session, session_id: str) -> ProblemSession:
    statement = (
        select(ProblemSession)
        .options(*_session_load_options())
        .where(ProblemSession.id == session_id)
    )
    session = database.scalar(statement)
    if session is None:
        raise ValueError(f"Session not found: {session_id}")
    return session


def _copy_session_scalars(target: ProblemSession, source: ProblemSession) -> None:
    target.display_name = source.display_name
    target.primary_ai_platform = source.primary_ai_platform
    target.rules_accepted = source.rules_accepted
    target.session_metadata = source.session_metadata
    target.raw_input = source.raw_input
    target.detected_domain = source.detected_domain
    target.detected_intent = source.detected_intent
    target.risk_level = source.risk_level
    target.classification = source.classification
    target.user_settings = source.user_settings
    target.status = source.status
    target.ended_at = source.ended_at


def _ensure_local_profile(database: Session) -> UserPromptProfile:
    statement = select(UserPromptProfile).where(UserPromptProfile.profile_key == "local")
    profile = database.scalar(statement)
    if profile is None:
        profile = UserPromptProfile(profile_key="local", display_name="Local profile")
        database.add(profile)
        database.flush()
    return profile


def _deleted_count(result) -> int:
    count = getattr(result, "rowcount", 0)
    return count if isinstance(count, int) and count > 0 else 0


store = DatabaseStore()


def check_database_connection() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            row = connection.execute(text("select current_database(), current_user")).one()
    except Exception as exc:  # pragma: no cover - health endpoint should degrade.
        return {
            "status": "unavailable",
            "detail": str(exc),
        }

    return {
        "status": "ok",
        "database": row[0],
        "user": row[1],
    }
