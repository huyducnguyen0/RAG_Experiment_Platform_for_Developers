from pydantic import BaseModel


class EvalQuestion(BaseModel):
    id: str
    question: str
    workspace_id: str
    expected_chunk_ids: list[str]
    top_k: int = 3
    notes: str = ""


class EvalQuestionListResponse(BaseModel):
    items: list[EvalQuestion]
    total: int


class EvalQuestionUploadResponse(BaseModel):
    workspace_id: str
    imported: int


class DeleteEvalQuestionResponse(BaseModel):
    deleted: bool
    workspace_id: str
    question_id: str
