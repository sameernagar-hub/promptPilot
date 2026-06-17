from fastapi import APIRouter, HTTPException

from app.schemas import (
    ConversationImportDeleteResponse,
    ConversationImportRequest,
    ConversationImportResponse,
)
from app.services.import_service import (
    create_conversation_import,
    delete_conversation_import,
    get_conversation_import,
    list_conversation_imports,
    reprocess_conversation_import,
)


router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("", response_model=ConversationImportResponse, status_code=201)
def create_import(payload: ConversationImportRequest) -> ConversationImportResponse:
    try:
        return create_conversation_import(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[ConversationImportResponse])
def list_imports() -> list[ConversationImportResponse]:
    return list_conversation_imports()


@router.get("/{import_id}", response_model=ConversationImportResponse)
def read_import(import_id: str) -> ConversationImportResponse:
    import_row = get_conversation_import(import_id)
    if import_row is None:
        raise HTTPException(status_code=404, detail="Import not found")
    return import_row


@router.post("/{import_id}/reprocess", response_model=ConversationImportResponse)
def reprocess_import(import_id: str) -> ConversationImportResponse:
    import_row = reprocess_conversation_import(import_id)
    if import_row is None:
        raise HTTPException(status_code=404, detail="Import not found")
    return import_row


@router.delete("/{import_id}", response_model=ConversationImportDeleteResponse)
def delete_import(import_id: str) -> ConversationImportDeleteResponse:
    result = delete_conversation_import(import_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Import not found")
    return result
