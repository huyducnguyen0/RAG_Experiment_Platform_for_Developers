from pydantic import BaseModel, Field

from app.schemas.phase_artifact import PhaseArtifact
from app.schemas.rag_config import RagConfigPreset


class ExperimentRunRequest(BaseModel):
    strategy: str = "keyword"
    config_id: str | None = None
    top_k: int = 5
    stage: str | None = None


class ExperimentCompareRequest(BaseModel):
    strategies: list[str] = Field(default_factory=lambda: ["keyword", "vector", "hybrid"])
    config_ids: list[str] = Field(default_factory=list)
    top_k: int = 5
    stage: str = "retriever_evaluation"
    candidate_pool_size: int = 5


class ExperimentMetrics(BaseModel):
    case_count: int
    hit_count: int
    hit_at_k: float
    recall_at_k: float
    precision_at_k: float
    mrr: float
    avg_latency_ms: float
    chunk_count: int = 0
    avg_chunk_size: float = 0.0
    min_chunk_size: int = 0
    max_chunk_size: int = 0
    coverage_ratio: float = 0.0
    answer_case_count: int = 0
    answer_reference_case_count: int = 0
    answer_present_rate: float = 0.0
    avg_answer_match_score: float = 0.0


class ExperimentCaseResult(BaseModel):
    question_id: str = ""
    question: str
    workspace_id: str
    top_k: int
    notes: str = ""
    expected_chunk_ids: list[str]
    returned_chunk_ids: list[str]
    returned_source_paths: list[str] = Field(default_factory=list)
    returned_doc_types: list[str] = Field(default_factory=list)
    label_type: str = "strong_chunk_ids"
    relevant_count: int
    hit: bool
    recall_at_k: float
    precision_at_k: float
    reciprocal_rank: float
    latency_ms: float
    generated_answer: str = ""
    reference_answer: str = ""
    source_count: int = 0
    answer_present: bool = False
    answer_match_score: float = 0.0


class ExperimentRunResponse(BaseModel):
    run_id: str
    workspace_id: str
    config_id: str = ""
    config_name: str = ""
    rag_stage: str = ""
    strategy: str
    top_k: int
    created_at: str
    metrics: ExperimentMetrics
    results: list[ExperimentCaseResult]
    report_markdown_path: str
    rag_config: RagConfigPreset | None = None


class ExperimentSummary(BaseModel):
    run_id: str
    workspace_id: str
    config_id: str = ""
    config_name: str = ""
    rag_stage: str = ""
    strategy: str
    top_k: int
    created_at: str
    metrics: ExperimentMetrics
    rag_config: RagConfigPreset | None = None


class ExperimentListResponse(BaseModel):
    items: list[ExperimentSummary]
    total: int


class ExperimentReportResponse(BaseModel):
    run_id: str
    workspace_id: str
    markdown: str


class ExperimentLeaderboardRow(BaseModel):
    rank: int
    run_id: str
    config_id: str
    config_name: str
    rag_stage: str
    strategy: str
    metrics: ExperimentMetrics
    score: float
    status: str
    verdict: str
    rag_config: RagConfigPreset | None = None


class ExperimentStrategyQuestionResult(BaseModel):
    config_id: str = ""
    config_name: str = ""
    strategy: str
    run_id: str
    hit: bool
    returned_chunk_ids: list[str]
    relevant_count: int
    recall_at_k: float
    precision_at_k: float
    reciprocal_rank: float
    latency_ms: float


class ExperimentQuestionComparisonRow(BaseModel):
    question_id: str
    question: str
    expected_chunk_ids: list[str]
    notes: str = ""
    winner: str | None
    status: str
    strategy_results: list[ExperimentStrategyQuestionResult]


class ExperimentComparisonSummary(BaseModel):
    stage: str
    total_configs: int
    candidate_pool_size: int
    kept_count: int
    best_config_id: str | None
    best_config_name: str | None
    fastest_config_name: str | None
    highest_recall_config_name: str | None
    recommendation: str


class ExperimentComparisonResponse(BaseModel):
    workspace_id: str
    stage: str
    top_k: int
    created_at: str
    best_strategy: str | None
    summary: ExperimentComparisonSummary
    phase_artifact: PhaseArtifact | None = None
    leaderboard: list[ExperimentLeaderboardRow]
    rag_configs: list[RagConfigPreset]
    question_comparisons: list[ExperimentQuestionComparisonRow]
    runs: list[ExperimentSummary]
