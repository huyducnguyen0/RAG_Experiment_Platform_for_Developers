from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from app.schemas.phase_artifact import PhaseArtifact, PhaseArtifactCandidate
from app.services.document_service import WORKSPACES_DIR


def save_phase_artifact(
    workspace_id: str,
    phase_id: str,
    candidate_pool_size: int,
    leaderboard: list[object],
    summary: dict,
    parent_artifact_id: str | None = None,
    parent_phase_id: str | None = None,
) -> PhaseArtifact:
    created_at = datetime.now(UTC).isoformat()
    artifact_id = f"artifact_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
    candidates = [_candidate_from_leaderboard_row(row) for row in leaderboard]
    kept_config_ids = [item.config_id for item in candidates if item.status == "kept"]
    input_config_ids = [item.config_id for item in candidates]
    pruned_config_ids = [item.config_id for item in candidates if item.status == "pruned"]
    best_candidate = candidates[0] if candidates else None

    artifact = PhaseArtifact(
        artifact_id=artifact_id,
        workspace_id=workspace_id,
        phase_id=phase_id,
        parent_artifact_id=parent_artifact_id,
        parent_phase_id=parent_phase_id,
        created_at=created_at,
        candidate_pool_size=candidate_pool_size,
        total_candidates=len(candidates),
        kept_count=len(kept_config_ids),
        input_config_ids=input_config_ids,
        kept_config_ids=kept_config_ids,
        pruned_config_ids=pruned_config_ids,
        best_config_id=best_candidate.config_id if best_candidate else None,
        best_config_name=best_candidate.config_name if best_candidate else None,
        candidates=candidates,
        summary=summary,
    )

    artifact_file = _workspace_phase_artifact_file(workspace_id, artifact_id)
    artifact_file.write_text(
        json.dumps(artifact.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return artifact


def list_phase_artifacts(workspace_id: str) -> list[PhaseArtifact]:
    items: list[PhaseArtifact] = []
    for file_path in sorted(_workspace_phase_artifact_dir(workspace_id).glob("artifact_*.json"), reverse=True):
        items.append(_load_phase_artifact_file(file_path))
    return items


def get_phase_artifact(workspace_id: str, artifact_id: str) -> PhaseArtifact:
    artifact_file = _workspace_phase_artifact_file(workspace_id, artifact_id)
    if not artifact_file.exists():
        raise HTTPException(status_code=404, detail="Phase artifact not found")
    return _load_phase_artifact_file(artifact_file)


def get_latest_phase_artifact(workspace_id: str, phase_id: str | None = None) -> PhaseArtifact | None:
    artifacts = list_phase_artifacts(workspace_id)
    if phase_id:
        selected_phase_id = phase_id.strip().lower()
        artifacts = [item for item in artifacts if item.phase_id == selected_phase_id]
    return artifacts[0] if artifacts else None


def _candidate_from_leaderboard_row(row: object) -> PhaseArtifactCandidate:
    return PhaseArtifactCandidate(
        rank=row.rank,
        run_id=row.run_id,
        config_id=row.config_id,
        config_name=row.config_name,
        strategy=row.strategy,
        chunking_type=row.rag_config.chunking.type if row.rag_config else "",
        chunking_params=row.rag_config.chunking.params if row.rag_config else {},
        retriever_type=row.rag_config.retriever.type if row.rag_config else "",
        score=row.score,
        status=row.status,
        verdict=row.verdict,
        hit_at_k=row.metrics.hit_at_k,
        recall_at_k=row.metrics.recall_at_k,
        precision_at_k=row.metrics.precision_at_k,
        mrr=row.metrics.mrr,
        avg_latency_ms=row.metrics.avg_latency_ms,
        chunk_count=row.metrics.chunk_count,
        avg_chunk_size=row.metrics.avg_chunk_size,
        min_chunk_size=row.metrics.min_chunk_size,
        max_chunk_size=row.metrics.max_chunk_size,
        coverage_ratio=row.metrics.coverage_ratio,
    )


def _workspace_phase_artifact_dir(workspace_id: str) -> Path:
    directory = WORKSPACES_DIR / workspace_id / "phase_artifacts"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _workspace_phase_artifact_file(workspace_id: str, artifact_id: str) -> Path:
    return _workspace_phase_artifact_dir(workspace_id) / f"{artifact_id}.json"


def _load_phase_artifact_file(file_path: Path) -> PhaseArtifact:
    return PhaseArtifact(**json.loads(file_path.read_text(encoding="utf-8")))
