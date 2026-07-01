from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.db import SessionLocal, store
from app.models import (
    ConversationImport,
    ImportedConversation,
    ImportedMessage,
    PromptIntelligenceReport,
    PromptingTraitSignal,
    TraitObservation,
    utc_now,
)
from app.schemas import (
    ConversationImportDeleteResponse,
    ConversationImportRequest,
    ConversationImportResponse,
    ImportedConversationResponse,
    ImportedMessageResponse,
)
from app.services.import_normalizer import NormalizedImport, normalize_import
from app.services.profile_analyzer import ensure_local_profile, refresh_prompt_profile


def create_conversation_import(payload: ConversationImportRequest) -> ConversationImportResponse:
    normalized = normalize_import(
        platform=payload.platform,
        source_type=payload.source_type,
        title=payload.title,
        raw_text=payload.raw_text,
    )
    with SessionLocal() as database:
        profile = ensure_local_profile(database)
        import_row = _build_import_row(normalized, profile.id)
        database.add(import_row)
        database.commit()
        import_id = import_row.id

    refresh_prompt_profile()
    response = get_conversation_import(import_id)
    if response is None:
        raise ValueError("Import was saved but could not be reloaded")
    store.record_audit_log(
        event_type="conversation_import_created",
        entity_type="conversation_import",
        entity_id=response.id,
        metadata={
            "platform": response.platform,
            "source_type": response.source_type,
            "redaction_status": response.redaction_status,
            "conversation_count": response.conversation_count,
            "message_count": response.message_count,
        },
    )
    return response


def list_conversation_imports() -> list[ConversationImportResponse]:
    with SessionLocal() as database:
        rows = list(
            database.scalars(
                select(ConversationImport)
                .options(_import_load_options())
                .order_by(ConversationImport.created_at.desc())
            )
        )
        return [_import_response(row) for row in rows]


def get_conversation_import(import_id: str) -> ConversationImportResponse | None:
    with SessionLocal() as database:
        row = database.scalar(
            select(ConversationImport)
            .options(_import_load_options())
            .where(ConversationImport.id == import_id)
        )
        return _import_response(row) if row else None


def delete_conversation_import(import_id: str) -> ConversationImportDeleteResponse | None:
    with SessionLocal() as database:
        row = database.scalar(
            select(ConversationImport)
            .options(_import_load_options())
            .where(ConversationImport.id == import_id)
        )
        if row is None:
            return None

        message_ids = [
            message.id
            for conversation in row.conversations
            for message in conversation.messages
        ]
        delete_metadata = {
            "platform": row.platform,
            "source_type": row.source_type,
            "conversation_count": len(row.conversations),
            "message_count": len(message_ids),
            "redaction_status": row.redaction_status,
        }
        if message_ids:
            database.execute(
                delete(PromptingTraitSignal).where(
                    PromptingTraitSignal.imported_message_id.in_(message_ids)
                )
            )
            database.execute(
                delete(TraitObservation).where(
                    TraitObservation.imported_message_id.in_(message_ids)
                )
            )
        database.execute(
            delete(PromptIntelligenceReport).where(
                PromptIntelligenceReport.import_id == import_id
            )
        )

        database.delete(row)
        database.commit()

    refresh_prompt_profile()
    store.record_audit_log(
        event_type="conversation_import_deleted",
        entity_type="conversation_import",
        entity_id=import_id,
        metadata=delete_metadata,
    )
    return ConversationImportDeleteResponse(id=import_id, deleted=True)


def reprocess_conversation_import(import_id: str) -> ConversationImportResponse | None:
    with SessionLocal() as database:
        row = database.scalar(
            select(ConversationImport).where(ConversationImport.id == import_id)
        )
        if row is None:
            return None
        row.updated_at = utc_now()
        database.commit()

    refresh_prompt_profile()
    response = get_conversation_import(import_id)
    if response:
        store.record_audit_log(
            event_type="conversation_import_reprocessed",
            entity_type="conversation_import",
            entity_id=response.id,
            metadata={
                "platform": response.platform,
                "source_type": response.source_type,
                "message_count": response.message_count,
            },
        )
    return response


def _build_import_row(normalized: NormalizedImport, profile_id: str) -> ConversationImport:
    import_row = ConversationImport(
        profile_id=profile_id,
        platform=normalized.platform,
        source_type=normalized.source_type,
        title=normalized.title,
        consent_status="user_provided",
        redaction_status=normalized.redaction_status,
        import_metadata=normalized.metadata,
    )

    for conversation in normalized.conversations:
        conversation_row = ImportedConversation(
            platform=conversation.platform,
            external_conversation_id=conversation.external_conversation_id,
            title=conversation.title,
            conversation_metadata=conversation.metadata,
        )
        for message in conversation.messages:
            conversation_row.messages.append(
                ImportedMessage(
                    role=message.role,
                    message_text=message.message_text,
                    redacted_text=message.redacted_text,
                    position=message.position,
                    message_timestamp=message.message_timestamp,
                    message_metadata=message.metadata,
                )
            )
        import_row.conversations.append(conversation_row)
    return import_row


def _import_response(row: ConversationImport) -> ConversationImportResponse:
    conversations = [
        ImportedConversationResponse(
            id=conversation.id,
            import_id=conversation.import_id,
            platform=conversation.platform,
            external_conversation_id=conversation.external_conversation_id,
            title=conversation.title,
            message_count=len(conversation.messages),
            messages=[
                ImportedMessageResponse(
                    id=message.id,
                    role=message.role,
                    text=message.redacted_text or message.message_text,
                    redacted=message.redacted_text is not None,
                    position=message.position,
                    message_timestamp=message.message_timestamp,
                    created_at=message.created_at,
                )
                for message in conversation.messages
            ],
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
        for conversation in row.conversations
    ]

    return ConversationImportResponse(
        id=row.id,
        profile_id=row.profile_id,
        platform=row.platform,
        source_type=row.source_type,
        title=row.title,
        consent_status=row.consent_status,
        redaction_status=row.redaction_status,
        conversation_count=len(conversations),
        message_count=sum(conversation.message_count for conversation in conversations),
        import_metadata=row.import_metadata,
        conversations=conversations,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _import_load_options():
    return selectinload(ConversationImport.conversations).selectinload(
        ImportedConversation.messages
    )
