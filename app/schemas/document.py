from pydantic import BaseModel


class DocumentSummary(BaseModel):
    id: str
    title: str
    file_name: str
    file_type: str
    content_length: int
    created_at: str


class DocumentDetail(DocumentSummary):
    content: str


class DeleteDocumentResponse(BaseModel):
    deleted: bool
    document_id: str
