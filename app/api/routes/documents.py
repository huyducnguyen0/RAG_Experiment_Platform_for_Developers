from fastapi import APIRouter, File, UploadFile

from app.schemas.document import (
    DeleteDocumentResponse,
    DocumentDetail,
    DocumentSummary,
)
from app.services.document_service import (
    delete_document,
    get_document,
    list_documents,
    save_uploaded_document,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentDetail)
def upload_document(file: UploadFile = File(...)):
    return save_uploaded_document(file)


@router.get("", response_model=list[DocumentSummary])
def get_documents():
    return list_documents()


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document_detail(document_id: str):
    return get_document(document_id)


@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
def remove_document(document_id: str):
    delete_document(document_id)
    return DeleteDocumentResponse(deleted=True, document_id=document_id)
