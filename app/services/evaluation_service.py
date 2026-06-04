from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
import re

from app.services.retrieval_service import prepare_retrieval_strategy, retrieve_relevant_chunks


@dataclass
class RetrievalEvalCase:
    question_id: str
    question: str
    workspace_id: str
    expected_chunk_ids: list[str]
    top_k: int = 5
    notes: str = ""
    expected_evidence_texts: list[str] | None = None
    reference_answer: str = ""
    keywords: list[str] | None = None
    category: str = ""
    label_type: str = "strong_chunk_ids"


@dataclass
class RetrievalEvalCaseResult:
    question_id: str
    question: str
    workspace_id: str
    top_k: int
    notes: str
    expected_chunk_ids: list[str]
    returned_chunk_ids: list[str]
    returned_source_paths: list[str]
    returned_doc_types: list[str]
    label_type: str
    relevant_count: int
    hit: bool
    recall_at_k: float
    precision_at_k: float
    reciprocal_rank: float
    latency_ms: float


def evaluate_retrieval(
    cases: list[RetrievalEvalCase],
    strategy: str = "keyword",
    chunks: list[dict] | None = None,
    relevance_mode: str = "chunk_id",
    retrieval_context_id: str | None = None,
) -> tuple[dict, list[RetrievalEvalCaseResult]]:
    if not cases:
        raise ValueError("At least one evaluation case is required")

    for workspace_id in sorted({case.workspace_id for case in cases}):
        prepare_retrieval_strategy(
            workspace_id=workspace_id,
            strategy=strategy,
            chunks=chunks,
            retrieval_context_id=retrieval_context_id,
        )

    results: list[RetrievalEvalCaseResult] = []

    for case in cases:
        started_at = perf_counter()
        retrieved = retrieve_relevant_chunks(
            question=case.question,
            top_k=case.top_k,
            workspace_id=case.workspace_id,
            strategy=strategy,
            chunks=chunks,
            retrieval_context_id=retrieval_context_id,
        )
        latency_ms = (perf_counter() - started_at) * 1000.0

        returned_chunk_ids = [item.chunk_id for item in retrieved.results]
        returned_source_paths = [item.source_path for item in retrieved.results]
        returned_doc_types = [item.doc_type for item in retrieved.results]
        evaluation_mode = _select_relevance_mode(case, relevance_mode)
        if evaluation_mode == "content_overlap":
            relevance = _content_overlap_relevance(
                returned_texts=[item.content for item in retrieved.results],
                expected_texts=case.expected_evidence_texts or [],
            )
            expected_count = len(case.expected_evidence_texts or [])
            relevant_count = relevance["relevant_count"]
            reciprocal_rank = relevance["reciprocal_rank"]
            recall_at_k = relevance["matched_expected_count"] / expected_count if expected_count else 0.0
        elif evaluation_mode == "weak_label":
            relevance = _weak_label_relevance(
                returned_texts=[item.content for item in retrieved.results],
                reference_answer=case.reference_answer,
                keywords=case.keywords or [],
            )
            relevant_count = relevance["relevant_count"]
            reciprocal_rank = relevance["reciprocal_rank"]
            recall_at_k = float(relevance["recall_proxy"])
        else:
            expected_set = set(case.expected_chunk_ids)
            relevant_count = len([chunk_id for chunk_id in returned_chunk_ids if chunk_id in expected_set])
            reciprocal_rank = _reciprocal_rank(
                returned_chunk_ids=returned_chunk_ids,
                expected_chunk_ids=expected_set,
            )
            recall_at_k = (
                relevant_count / len(expected_set) if expected_set else 0.0
            )

        hit = relevant_count > 0
        precision_at_k = (
            relevant_count / case.top_k if case.top_k > 0 else 0.0
        )

        results.append(
            RetrievalEvalCaseResult(
                question_id=case.question_id,
                question=case.question,
                workspace_id=case.workspace_id,
                top_k=case.top_k,
                notes=case.notes,
                expected_chunk_ids=case.expected_chunk_ids,
                returned_chunk_ids=returned_chunk_ids,
                returned_source_paths=returned_source_paths,
                returned_doc_types=returned_doc_types,
                label_type=case.label_type,
                relevant_count=relevant_count,
                hit=hit,
                recall_at_k=recall_at_k,
                precision_at_k=precision_at_k,
                reciprocal_rank=reciprocal_rank,
                latency_ms=latency_ms,
            )
        )

    summary = _summarize_results(results)
    summary.update(_summarize_chunks(chunks or []))
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


def _select_relevance_mode(
    case: RetrievalEvalCase,
    relevance_mode: str,
) -> str:
    if relevance_mode == "chunk_id":
        return "chunk_id"
    if relevance_mode == "content_overlap":
        return "content_overlap" if case.expected_evidence_texts else "weak_label"
    if case.expected_chunk_ids:
        return "chunk_id"
    if case.expected_evidence_texts:
        return "content_overlap"
    return "weak_label"


def _content_overlap_relevance(
    returned_texts: list[str],
    expected_texts: list[str],
) -> dict[str, int | float]:
    if not returned_texts or not expected_texts:
        return {
            "relevant_count": 0,
            "matched_expected_count": 0,
            "reciprocal_rank": 0.0,
        }

    expected_token_sets = [_token_set(text) for text in expected_texts]
    matched_expected_indexes: set[int] = set()
    relevant_count = 0
    reciprocal_rank = 0.0

    for rank, returned_text in enumerate(returned_texts, start=1):
        returned_tokens = _token_set(returned_text)
        if not returned_tokens:
            continue

        is_relevant = False
        for expected_index, expected_tokens in enumerate(expected_token_sets):
            if not expected_tokens:
                continue
            overlap_ratio = len(returned_tokens & expected_tokens) / len(expected_tokens)
            if overlap_ratio >= 0.25:
                is_relevant = True
                matched_expected_indexes.add(expected_index)

        if is_relevant:
            relevant_count += 1
            if reciprocal_rank == 0.0:
                reciprocal_rank = 1.0 / rank

    return {
        "relevant_count": relevant_count,
        "matched_expected_count": len(matched_expected_indexes),
        "reciprocal_rank": reciprocal_rank,
    }


def _weak_label_relevance(
    returned_texts: list[str],
    reference_answer: str,
    keywords: list[str],
) -> dict[str, int | float]:
    if not returned_texts:
        return {
            "relevant_count": 0,
            "reciprocal_rank": 0.0,
            "recall_proxy": 0.0,
        }

    normalized_keywords = _token_set(" ".join(keywords))
    reference_tokens = _token_set(reference_answer)
    matched_keywords: set[str] = set()
    relevant_count = 0
    reciprocal_rank = 0.0
    best_reference_overlap = 0.0

    for rank, returned_text in enumerate(returned_texts, start=1):
        returned_tokens = _token_set(returned_text)
        if not returned_tokens:
            continue

        keyword_hits = returned_tokens & normalized_keywords
        matched_keywords.update(keyword_hits)
        reference_overlap = (
            len(returned_tokens & reference_tokens) / len(reference_tokens)
            if reference_tokens
            else 0.0
        )
        best_reference_overlap = max(best_reference_overlap, reference_overlap)
        is_relevant = bool(keyword_hits) or reference_overlap >= 0.25
        if is_relevant:
            relevant_count += 1
            if reciprocal_rank == 0.0:
                reciprocal_rank = 1.0 / rank

    keyword_coverage = (
        len(matched_keywords) / len(normalized_keywords)
        if normalized_keywords
        else 0.0
    )
    recall_proxy = max(keyword_coverage, best_reference_overlap)
    if relevant_count > 0 and recall_proxy == 0.0:
        recall_proxy = 1.0

    return {
        "relevant_count": relevant_count,
        "reciprocal_rank": reciprocal_rank,
        "recall_proxy": recall_proxy,
    }


def _token_set(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) >= 2
    }


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


def _summarize_chunks(chunks: list[dict]) -> dict:
    if not chunks:
        return {
            "chunk_count": 0,
            "avg_chunk_size": 0.0,
            "min_chunk_size": 0,
            "max_chunk_size": 0,
            "coverage_ratio": 0.0,
        }

    sizes = [len(chunk.get("content", "")) for chunk in chunks]
    return {
        "chunk_count": len(chunks),
        "avg_chunk_size": _mean([float(size) for size in sizes]),
        "min_chunk_size": min(sizes),
        "max_chunk_size": max(sizes),
        "coverage_ratio": _coverage_ratio(chunks),
    }


def _coverage_ratio(chunks: list[dict]) -> float:
    by_document: dict[str, dict] = {}
    for chunk in chunks:
        document_id = str(chunk.get("document_id", ""))
        start_index = chunk.get("start_index")
        end_index = chunk.get("end_index")
        content_length = int(chunk.get("document_content_length", 0) or 0)
        if not document_id or start_index is None or end_index is None or content_length <= 0:
            continue

        item = by_document.setdefault(
            document_id,
            {
                "content_length": content_length,
                "intervals": [],
            },
        )
        item["content_length"] = max(item["content_length"], content_length)
        item["intervals"].append((int(start_index), int(end_index)))

    covered_total = 0
    document_total = 0
    for item in by_document.values():
        document_total += item["content_length"]
        covered_total += _merged_interval_length(item["intervals"])

    return covered_total / document_total if document_total else 0.0


def _merged_interval_length(intervals: list[tuple[int, int]]) -> int:
    if not intervals:
        return 0

    sorted_intervals = sorted(intervals)
    merged: list[tuple[int, int]] = []
    for start, end in sorted_intervals:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            previous_start, previous_end = merged[-1]
            merged[-1] = (previous_start, max(previous_end, end))

    return sum(end - start for start, end in merged)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
