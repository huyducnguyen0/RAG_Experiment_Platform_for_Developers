from pydantic import BaseModel


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    original_text: str = ""
    headline: str = ""
    summary: str = ""
    start_index: int
    end_index: int
    content_length: int
    source_path: str = ""
    relative_path: str = ""
    folder_path: str = ""
    doc_type: str = ""
    file_extension: str = ""
    chunking_strategy: str = "fixed"
    chunk_size: int = 0
    chunk_overlap: int = 0


class DocumentSummary(BaseModel):
    id: str
    workspace_id: str | None = None
    title: str
    file_name: str
    file_type: str
    source_path: str = ""
    relative_path: str = ""
    folder_path: str = ""
    doc_type: str = ""
    file_extension: str = ""
    content_length: int
    chunk_count: int
    created_at: str


class DocumentDetail(DocumentSummary):
    content: str
    chunks: list[DocumentChunk] = []


class DeleteDocumentResponse(BaseModel):
    deleted: bool
    document_id: str


class FolderUploadResponse(BaseModel):
    workspace_id: str
    imported: int
    skipped: int
    documents: list[DocumentSummary]
