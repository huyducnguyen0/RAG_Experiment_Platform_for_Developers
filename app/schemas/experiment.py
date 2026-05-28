from pydantic import BaseModel


class ExperimentRunRequest(BaseModel):
    strategy: str = "keyword"
    top_k: int = 3


class ExperimentMetrics(BaseModel):
    case_count: int
    hit_count: int
    hit_at_k: float
    recall_at_k: float
    precision_at_k: float
    mrr: float
    avg_latency_ms: float


class ExperimentCaseResult(BaseModel):
    question: str
    workspace_id: str
    top_k: int
    expected_chunk_ids: list[str]
    returned_chunk_ids: list[str]
    relevant_count: int
    hit: bool
    recall_at_k: float
    precision_at_k: float
    reciprocal_rank: float
    latency_ms: float


class ExperimentRunResponse(BaseModel):
    run_id: str
    workspace_id: str
    strategy: str
    top_k: int
    created_at: str
    metrics: ExperimentMetrics
    results: list[ExperimentCaseResult]
    report_markdown_path: str


class ExperimentSummary(BaseModel):
    run_id: str
    workspace_id: str
    strategy: str
    top_k: int
    created_at: str
    metrics: ExperimentMetrics


class ExperimentListResponse(BaseModel):
    items: list[ExperimentSummary]
    total: int


class ExperimentReportResponse(BaseModel):
    run_id: str
    workspace_id: str
    markdown: str
