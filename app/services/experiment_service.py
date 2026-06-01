from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from app.schemas.experiment import (
    ExperimentComparisonResponse,
    ExperimentCaseResult,
    ExperimentMetrics,
    ExperimentRunResponse,
    ExperimentSummary,
)
from app.services.document_service import WORKSPACES_DIR
from app.services.eval_question_service import list_eval_questions, repair_eval_questions_missing_chunk_ids
from app.services.evaluation_service import RetrievalEvalCase, evaluate_retrieval
from app.services.retrieval_service import SUPPORTED_RETRIEVAL_STRATEGIES


def run_workspace_experiment(
    workspace_id: str,
    strategy: str,
    top_k: int,
) -> ExperimentRunResponse:
    selected_strategy = strategy.strip().lower()
    if selected_strategy not in SUPPORTED_RETRIEVAL_STRATEGIES:
        allowed = ", ".join(sorted(SUPPORTED_RETRIEVAL_STRATEGIES))
        raise HTTPException(status_code=400, detail=f"Unsupported strategy. Allowed: {allowed}")
    if top_k <= 0:
        raise HTTPException(status_code=400, detail="top_k must be greater than 0")

    eval_questions = list_eval_questions(workspace_id)
    if not eval_questions:
        raise HTTPException(status_code=400, detail="No golden questions found in this workspace")
    if _has_missing_expected_chunk_ids(eval_questions):
        repair_eval_questions_missing_chunk_ids(workspace_id)
        eval_questions = list_eval_questions(workspace_id)

    invalid_question_ids = [
        item.id
        for item in eval_questions
        if not item.expected_chunk_ids
        or not any(str(chunk_id).strip() for chunk_id in item.expected_chunk_ids)
    ]
    if invalid_question_ids:
        preview_ids = ", ".join(invalid_question_ids[:5])
        suffix = "..." if len(invalid_question_ids) > 5 else ""
        raise HTTPException(
            status_code=400,
            detail=(
                "Golden questions are missing expected_chunk_ids. "
                f"Fix and re-upload the dataset before running experiments. "
                f"Example question ids: {preview_ids}{suffix}"
            ),
        )

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

    summary, results = evaluate_retrieval(cases=cases, strategy=selected_strategy)
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


def run_workspace_experiment_comparison(
    workspace_id: str,
    strategies: list[str],
    top_k: int,
) -> ExperimentComparisonResponse:
    selected_strategies = _normalize_strategy_list(strategies)
    if top_k <= 0:
        raise HTTPException(status_code=400, detail="top_k must be greater than 0")

    runs = [
        run_workspace_experiment(
            workspace_id=workspace_id,
            strategy=strategy,
            top_k=top_k,
        )
        for strategy in selected_strategies
    ]
    summaries = [_to_summary(run) for run in runs]
    ranked_summaries = sorted(
        summaries,
        key=lambda item: (
            item.metrics.hit_at_k,
            item.metrics.mrr,
            item.metrics.recall_at_k,
            -item.metrics.avg_latency_ms,
        ),
        reverse=True,
    )
    best_strategy = ranked_summaries[0].strategy if ranked_summaries else None

    return ExperimentComparisonResponse(
        workspace_id=workspace_id,
        top_k=top_k,
        created_at=datetime.now(UTC).isoformat(),
        best_strategy=best_strategy,
        runs=ranked_summaries,
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


def _normalize_strategy_list(strategies: list[str]) -> list[str]:
    normalized: list[str] = []
    for strategy in strategies:
        selected_strategy = strategy.strip().lower()
        if not selected_strategy:
            continue
        if selected_strategy not in SUPPORTED_RETRIEVAL_STRATEGIES:
            allowed = ", ".join(sorted(SUPPORTED_RETRIEVAL_STRATEGIES))
            raise HTTPException(status_code=400, detail=f"Unsupported strategy. Allowed: {allowed}")
        if selected_strategy not in normalized:
            normalized.append(selected_strategy)

    if not normalized:
        raise HTTPException(status_code=400, detail="At least one strategy is required")

    return normalized


def _to_summary(run: ExperimentRunResponse) -> ExperimentSummary:
    return ExperimentSummary(
        run_id=run.run_id,
        workspace_id=run.workspace_id,
        strategy=run.strategy,
        top_k=run.top_k,
        created_at=run.created_at,
        metrics=run.metrics,
    )


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
        "notes": item.notes,
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
    failed_results = [result for result in payload["results"] if not result["hit"]]
    zero_return_results = [result for result in payload["results"] if not result["returned_chunk_ids"]]
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
        f"- Failed Cases: {len(failed_results)}",
        f"- Empty Retrieval Cases: {len(zero_return_results)}",
        f"- Hit@k: {metrics['hit_at_k']:.4f}",
        f"- Recall@k: {metrics['recall_at_k']:.4f}",
        f"- Precision@k: {metrics['precision_at_k']:.4f}",
        f"- MRR: {metrics['mrr']:.4f}",
        f"- Avg Latency (ms): {metrics['avg_latency_ms']:.2f}",
        "",
    ]

    if failed_results:
        lines.extend(
            [
                "## Failed Cases Overview",
                "",
            ]
        )

        for index, result in enumerate(failed_results, start=1):
            lines.extend(
                [
                    f"### Failed Case {index}",
                    f"- Question: {result['question']}",
                    f"- Expected Count: {len(result['expected_chunk_ids'])}",
                    f"- Returned Count: {len(result['returned_chunk_ids'])}",
                    f"- Expected: {', '.join(result['expected_chunk_ids']) if result['expected_chunk_ids'] else '(none)'}",
                    f"- Returned: {', '.join(result['returned_chunk_ids']) if result['returned_chunk_ids'] else '(none)'}",
                    f"- Notes: {result['notes'] or '(none)'}",
                    "",
                ]
            )

    lines.extend(
        [
        "## Per-Question Results",
        "",
        ]
    )

    for index, result in enumerate(payload["results"], start=1):
        lines.extend(
            [
                f"### Case {index}",
                f"- Question: {result['question']}",
                f"- Status: {'PASS' if result['hit'] else 'FAIL'}",
                f"- Notes: {result['notes'] or '(none)'}",
                f"- Expected Count: {len(result['expected_chunk_ids'])}",
                f"- Returned Count: {len(result['returned_chunk_ids'])}",
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


def _has_missing_expected_chunk_ids(eval_questions: list[object]) -> bool:
    return any(
        not item.expected_chunk_ids
        or not any(str(chunk_id).strip() for chunk_id in item.expected_chunk_ids)
        for item in eval_questions
    )
