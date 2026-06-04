from pydantic import BaseModel


class EvalQuestion(BaseModel):
    id: str
    question: str
    workspace_id: str
    expected_chunk_ids: list[str] = []
    reference_answer: str = ""
    keywords: list[str] = []
    category: str = ""
    gold_evidence_text: str = ""
    label_type: str = "strong_chunk_ids"
    top_k: int = 5
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
