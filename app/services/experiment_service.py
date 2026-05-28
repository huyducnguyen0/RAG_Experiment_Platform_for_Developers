from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from app.schemas.experiment import (
    ExperimentCaseResult,
    ExperimentMetrics,
    ExperimentRunResponse,
    ExperimentSummary,
)
from app.services.document_service import WORKSPACES_DIR
from app.services.eval_question_service import list_eval_questions
from app.services.evaluation_service import RetrievalEvalCase, evaluate_keyword_retrieval


def run_workspace_experiment(
    workspace_id: str,
    strategy: str,
    top_k: int,
) -> ExperimentRunResponse:
    selected_strategy = strategy.strip().lower()
    if selected_strategy != "keyword":
        raise HTTPException(status_code=400, detail="Only 'keyword' strategy is supported in this phase")
    if top_k <= 0:
        raise HTTPException(status_code=400, detail="top_k must be greater than 0")

    eval_questions = list_eval_questions(workspace_id)
    if not eval_questions:
        raise HTTPException(status_code=400, detail="No golden questions found in this workspace")

    cases = [
        RetrievalEvalCase(
            question=item.question,
            workspace_id=workspace_id,
            expected_chunk_ids=item.expected_chunk_ids,
            top_k=top_k,
            notes=item.notes,
        )
        for item in eval_questions
    ]

    summary, results = evaluate_keyword_retrieval(cases)
    created_at = datetime.now(UTC).isoformat()
    run_id = f"run_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"

    payload = {
        "run_id": run_id,
        "workspace_id": workspace_id,
        "strategy": selected_strategy,
        "top_k": top_k,
        "created_at": created_at,
        "metrics": summary,
        "results": [_serialize_result(item) for item in results],
    }

    experiment_path = _workspace_experiment_file(workspace_id, run_id)
    experiment_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report_path = _workspace_report_file(workspace_id, run_id)
    report_markdown = _build_markdown_report(payload)
    report_path.write_text(report_markdown, encoding="utf-8")

    return ExperimentRunResponse(
        run_id=run_id,
        workspace_id=workspace_id,
        strategy=selected_strategy,
        top_k=top_k,
        created_at=created_at,
        metrics=ExperimentMetrics(**summary),
        results=[ExperimentCaseResult(**_serialize_result(item)) for item in results],
        report_markdown_path=str(report_path),
    )


def list_workspace_experiments(workspace_id: str) -> list[ExperimentSummary]:
    experiment_dir = _workspace_experiment_dir(workspace_id)
    items: list[ExperimentSummary] = []

    for file_path in sorted(experiment_dir.glob("run_*.json"), reverse=True):
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        items.append(
            ExperimentSummary(
                run_id=payload["run_id"],
                workspace_id=payload["workspace_id"],
                strategy=payload["strategy"],
                top_k=payload["top_k"],
                created_at=payload["created_at"],
                metrics=ExperimentMetrics(**payload["metrics"]),
            )
        )

    return items


def get_workspace_experiment(workspace_id: str, run_id: str) -> ExperimentRunResponse:
    payload = _load_experiment_payload(workspace_id, run_id)
    return ExperimentRunResponse(
        run_id=payload["run_id"],
        workspace_id=payload["workspace_id"],
        strategy=payload["strategy"],
        top_k=payload["top_k"],
        created_at=payload["created_at"],
        metrics=ExperimentMetrics(**payload["metrics"]),
        results=[ExperimentCaseResult(**item) for item in payload["results"]],
        report_markdown_path=str(_workspace_report_file(workspace_id, run_id)),
    )


def get_workspace_report_markdown(workspace_id: str, run_id: str) -> str:
    report_file = _workspace_report_file(workspace_id, run_id)
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return report_file.read_text(encoding="utf-8")


def _load_experiment_payload(workspace_id: str, run_id: str) -> dict:
    experiment_file = _workspace_experiment_file(workspace_id, run_id)
    if not experiment_file.exists():
        raise HTTPException(status_code=404, detail="Experiment run not found")
    return json.loads(experiment_file.read_text(encoding="utf-8"))


def _workspace_experiment_dir(workspace_id: str) -> Path:
    directory = WORKSPACES_DIR / workspace_id / "experiments"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _workspace_experiment_file(workspace_id: str, run_id: str) -> Path:
    return _workspace_experiment_dir(workspace_id) / f"{run_id}.json"


def _workspace_report_file(workspace_id: str, run_id: str) -> Path:
    report_dir = WORKSPACES_DIR / workspace_id / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir / f"{run_id}.md"


def _serialize_result(item: object) -> dict:
    return {
        "question": item.question,
        "workspace_id": item.workspace_id,
        "top_k": item.top_k,
        "expected_chunk_ids": item.expected_chunk_ids,
        "returned_chunk_ids": item.returned_chunk_ids,
        "relevant_count": item.relevant_count,
        "hit": item.hit,
        "recall_at_k": item.recall_at_k,
        "precision_at_k": item.precision_at_k,
        "reciprocal_rank": item.reciprocal_rank,
        "latency_ms": item.latency_ms,
    }


def _build_markdown_report(payload: dict) -> str:
    metrics = payload["metrics"]
    lines = [
        "# Workspace Retrieval Experiment Report",
        "",
        f"- Run ID: {payload['run_id']}",
        f"- Workspace: {payload['workspace_id']}",
        f"- Strategy: {payload['strategy']}",
        f"- Top K: {payload['top_k']}",
        f"- Created At (UTC): {payload['created_at']}",
        "",
        "## Metrics",
        "",
        f"- Cases: {metrics['case_count']}",
        f"- Hits: {metrics['hit_count']}",
        f"- Hit@k: {metrics['hit_at_k']:.4f}",
        f"- Recall@k: {metrics['recall_at_k']:.4f}",
        f"- Precision@k: {metrics['precision_at_k']:.4f}",
        f"- MRR: {metrics['mrr']:.4f}",
        f"- Avg Latency (ms): {metrics['avg_latency_ms']:.2f}",
        "",
        "## Per-Question Results",
        "",
    ]

    for index, result in enumerate(payload["results"], start=1):
        lines.extend(
            [
                f"### Case {index}",
                f"- Question: {result['question']}",
                f"- Returned: {', '.join(result['returned_chunk_ids']) if result['returned_chunk_ids'] else '(none)'}",
                f"- Expected: {', '.join(result['expected_chunk_ids']) if result['expected_chunk_ids'] else '(none)'}",
                f"- Hit: {result['hit']}",
                f"- Recall@k: {result['recall_at_k']:.4f}",
                f"- Precision@k: {result['precision_at_k']:.4f}",
                f"- RR: {result['reciprocal_rank']:.4f}",
                f"- Latency (ms): {result['latency_ms']:.2f}",
                "",
            ]
        )

    return "\n".join(lines)
