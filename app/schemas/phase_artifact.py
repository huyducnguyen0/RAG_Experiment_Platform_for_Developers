from typing import Any

from pydantic import BaseModel, Field


class PhaseArtifactCandidate(BaseModel):
    rank: int
    run_id: str
    config_id: str
    config_name: str
    strategy: str
    chunking_type: str = ""
    chunking_params: dict[str, Any] = Field(default_factory=dict)
    retriever_type: str = ""
    score: float
    status: str
    verdict: str
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


class PhaseArtifact(BaseModel):
    artifact_id: str
    workspace_id: str
    phase_id: str
    parent_artifact_id: str | None = None
    parent_phase_id: str | None = None
    created_at: str
    candidate_pool_size: int
    total_candidates: int
    kept_count: int
    input_config_ids: list[str]
    kept_config_ids: list[str]
    pruned_config_ids: list[str]
    best_config_id: str | None
    best_config_name: str | None
    candidates: list[PhaseArtifactCandidate]
    summary: dict[str, Any] = Field(default_factory=dict)


class PhaseArtifactListResponse(BaseModel):
    items: list[PhaseArtifact]
    total: int
