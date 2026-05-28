import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.evaluation_service import (
    RetrievalEvalCase,
    evaluate_keyword_retrieval,
)

DATASET_PATH = Path("eval/golden_questions.jsonl")


def load_cases(dataset_path: Path) -> list[RetrievalEvalCase]:
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}. Create eval/golden_questions.jsonl first."
        )

    cases: list[RetrievalEvalCase] = []

    for line_number, raw_line in enumerate(
        dataset_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line:
            continue

        payload = json.loads(line)
        question = payload.get("question", "").strip()
        workspace_id = payload.get("workspace_id", "").strip()
        expected_chunk_ids = payload.get("expected_chunk_ids", [])
        top_k = int(payload.get("top_k", 3))
        notes = payload.get("notes", "")

        if not question:
            raise ValueError(f"Line {line_number}: question is required")
        if not workspace_id:
            raise ValueError(f"Line {line_number}: workspace_id is required")
        if not isinstance(expected_chunk_ids, list):
            raise ValueError(f"Line {line_number}: expected_chunk_ids must be a list")

        cases.append(
            RetrievalEvalCase(
                question=question,
                workspace_id=workspace_id,
                expected_chunk_ids=[str(item) for item in expected_chunk_ids],
                top_k=top_k,
                notes=str(notes),
            )
        )

    if not cases:
        raise ValueError("Dataset is empty. Add at least one JSONL row.")

    return cases


def print_report(summary: dict, results: list) -> None:
    print("\n" + "=" * 72)
    print("KEYWORD RETRIEVAL BASELINE REPORT")
    print("=" * 72)
    print(f"Cases: {summary['case_count']}")
    print(f"Hits: {summary['hit_count']}")
    print(f"Hit@k: {summary['hit_at_k']:.4f}")
    print(f"Recall@k: {summary['recall_at_k']:.4f}")
    print(f"Precision@k: {summary['precision_at_k']:.4f}")
    print(f"MRR: {summary['mrr']:.4f}")
    print(f"Avg latency (ms): {summary['avg_latency_ms']:.2f}")
    print("-" * 72)

    for index, result in enumerate(results, start=1):
        print(f"[Case {index}]")
        print(f"Question: {result.question}")
        print(f"Workspace: {result.workspace_id}")
        print(f"Top-k: {result.top_k}")
        print(f"Expected chunk ids: {result.expected_chunk_ids}")
        print(f"Returned chunk ids: {result.returned_chunk_ids}")
        print(
            "Metrics: "
            f"hit={result.hit}, "
            f"recall@k={result.recall_at_k:.4f}, "
            f"precision@k={result.precision_at_k:.4f}, "
            f"rr={result.reciprocal_rank:.4f}, "
            f"latency_ms={result.latency_ms:.2f}"
        )
        print("-" * 72)


def main() -> None:
    cases = load_cases(DATASET_PATH)
    summary, results = evaluate_keyword_retrieval(cases)
    print_report(summary, results)


if __name__ == "__main__":
    main()
