from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from app.services.retrieval_service import prepare_retrieval_strategy, retrieve_relevant_chunks


@dataclass
class RetrievalEvalCase:
    question: str
    workspace_id: str
    expected_chunk_ids: list[str]
    top_k: int = 3
    notes: str = ""


@dataclass
class RetrievalEvalCaseResult:
    question: str
    workspace_id: str
    top_k: int
    notes: str
    expected_chunk_ids: list[str]
    returned_chunk_ids: list[str]
    relevant_count: int
    hit: bool
    recall_at_k: float
    precision_at_k: float
    reciprocal_rank: float
    latency_ms: float


def evaluate_retrieval(
    cases: list[RetrievalEvalCase],
    strategy: str = "keyword",
) -> tuple[dict, list[RetrievalEvalCaseResult]]:
    if not cases:
        raise ValueError("At least one evaluation case is required")

    for workspace_id in sorted({case.workspace_id for case in cases}):
        prepare_retrieval_strategy(workspace_id=workspace_id, strategy=strategy)

    results: list[RetrievalEvalCaseResult] = []

    for case in cases:
        started_at = perf_counter()
        retrieved = retrieve_relevant_chunks(
            question=case.question,
            top_k=case.top_k,
            workspace_id=case.workspace_id,
            strategy=strategy,
        )
        latency_ms = (perf_counter() - started_at) * 1000.0

        returned_chunk_ids = [item.chunk_id for item in retrieved.results]
        expected_set = set(case.expected_chunk_ids)
        relevant_count = len([chunk_id for chunk_id in returned_chunk_ids if chunk_id in expected_set])
        hit = relevant_count > 0
        recall_at_k = (
            relevant_count / len(expected_set) if expected_set else 0.0
        )
        precision_at_k = (
            relevant_count / case.top_k if case.top_k > 0 else 0.0
        )
        reciprocal_rank = _reciprocal_rank(
            returned_chunk_ids=returned_chunk_ids,
            expected_chunk_ids=expected_set,
        )

        results.append(
            RetrievalEvalCaseResult(
                question=case.question,
                workspace_id=case.workspace_id,
                top_k=case.top_k,
                notes=case.notes,
                expected_chunk_ids=case.expected_chunk_ids,
                returned_chunk_ids=returned_chunk_ids,
                relevant_count=relevant_count,
                hit=hit,
                recall_at_k=recall_at_k,
                precision_at_k=precision_at_k,
                reciprocal_rank=reciprocal_rank,
                latency_ms=latency_ms,
            )
        )

    summary = _summarize_results(results)
    return summary, results


def evaluate_keyword_retrieval(
    cases: list[RetrievalEvalCase],
) -> tuple[dict, list[RetrievalEvalCaseResult]]:
    return evaluate_retrieval(cases=cases, strategy="keyword")


def _reciprocal_rank(
    returned_chunk_ids: list[str],
    expected_chunk_ids: set[str],
) -> float:
    for index, chunk_id in enumerate(returned_chunk_ids, start=1):
        if chunk_id in expected_chunk_ids:
            return 1.0 / index

    return 0.0


def _summarize_results(results: list[RetrievalEvalCaseResult]) -> dict:
    case_count = len(results)
    hit_count = sum(1 for result in results if result.hit)

    return {
        "case_count": case_count,
        "hit_count": hit_count,
        "hit_at_k": hit_count / case_count if case_count else 0.0,
        "recall_at_k": _mean([result.recall_at_k for result in results]),
        "precision_at_k": _mean([result.precision_at_k for result in results]),
        "mrr": _mean([result.reciprocal_rank for result in results]),
        "avg_latency_ms": _mean([result.latency_ms for result in results]),
    }


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
