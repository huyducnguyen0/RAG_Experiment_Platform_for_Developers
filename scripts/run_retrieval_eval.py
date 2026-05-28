import json
from pathlib import Path
import sys
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.evaluation_service import (
    RetrievalEvalCase,
    evaluate_keyword_retrieval,
)

DATASET_PATH = Path("eval/golden_questions.jsonl")
REPORTS_DIR = Path("reports")


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


def export_report_files(summary: dict, results: list) -> tuple[Path, Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = REPORTS_DIR / f"retrieval_eval_{timestamp}.json"
    md_path = REPORTS_DIR / f"retrieval_eval_{timestamp}.md"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "strategy": "keyword",
        "summary": summary,
        "cases": [
            {
                "question": result.question,
                "workspace_id": result.workspace_id,
                "top_k": result.top_k,
                "expected_chunk_ids": result.expected_chunk_ids,
                "returned_chunk_ids": result.returned_chunk_ids,
                "relevant_count": result.relevant_count,
                "hit": result.hit,
                "recall_at_k": result.recall_at_k,
                "precision_at_k": result.precision_at_k,
                "reciprocal_rank": result.reciprocal_rank,
                "latency_ms": result.latency_ms,
            }
            for result in results
        ],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    markdown_lines = [
        "# Retrieval Evaluation Report",
        "",
        f"- Generated at (UTC): {payload['generated_at_utc']}",
        "- Strategy: keyword",
        "",
        "## Summary",
        "",
        f"- Cases: {summary['case_count']}",
        f"- Hits: {summary['hit_count']}",
        f"- Hit@k: {summary['hit_at_k']:.4f}",
        f"- Recall@k: {summary['recall_at_k']:.4f}",
        f"- Precision@k: {summary['precision_at_k']:.4f}",
        f"- MRR: {summary['mrr']:.4f}",
        f"- Avg latency (ms): {summary['avg_latency_ms']:.2f}",
        "",
        "## Per-case Results",
        "",
    ]

    for index, result in enumerate(results, start=1):
        markdown_lines.extend(
            [
                f"### Case {index}",
                "",
                f"- Question: {result.question}",
                f"- Workspace: {result.workspace_id}",
                f"- Top-k: {result.top_k}",
                f"- Expected chunk ids: {', '.join(result.expected_chunk_ids) if result.expected_chunk_ids else '(empty)'}",
                f"- Returned chunk ids: {', '.join(result.returned_chunk_ids) if result.returned_chunk_ids else '(empty)'}",
                f"- Hit: {result.hit}",
                f"- Recall@k: {result.recall_at_k:.4f}",
                f"- Precision@k: {result.precision_at_k:.4f}",
                f"- Reciprocal rank: {result.reciprocal_rank:.4f}",
                f"- Latency (ms): {result.latency_ms:.2f}",
                "",
            ]
        )

    md_path.write_text("\n".join(markdown_lines), encoding="utf-8")
    return json_path, md_path


def main() -> None:
    cases = load_cases(DATASET_PATH)
    summary, results = evaluate_keyword_retrieval(cases)
    print_report(summary, results)
    json_path, md_path = export_report_files(summary=summary, results=results)
    print(f"Saved JSON report: {json_path}")
    print(f"Saved Markdown report: {md_path}")


if __name__ == "__main__":
    main()
