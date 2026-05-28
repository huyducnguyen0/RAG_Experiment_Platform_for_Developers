from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    question: str
    top_k: int = Field(default=3, ge=1, le=10)


class RetrievedChunk(BaseModel):
    document_id: str
    document_title: str
    chunk_id: str
    chunk_index: int
    score: int
    content: str


class RetrieveResponse(BaseModel):
    query: str
    results: list[RetrievedChunk]
