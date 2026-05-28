from pydantic import BaseModel


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    start_index: int
    end_index: int
    content_length: int


class DocumentSummary(BaseModel):
    id: str
    title: str
    file_name: str
    file_type: str
    content_length: int
    chunk_count: int
    created_at: str


class DocumentDetail(DocumentSummary):
    content: str
    chunks: list[DocumentChunk] = []


class DeleteDocumentResponse(BaseModel):
    deleted: bool
    document_id: str
