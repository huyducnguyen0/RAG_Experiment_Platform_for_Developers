import argparse
import csv
import json
from pathlib import Path


def parse_chunk_ids(raw_value: str) -> list[str]:
    return [item.strip() for item in raw_value.split("|") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build final golden_questions.jsonl from mapping CSV.",
    )
    parser.add_argument(
        "--mapping",
        default="sample_data/squad_eval_pack/golden_questions_mapping.csv",
        help="Path to mapping CSV.",
    )
    parser.add_argument(
        "--output",
        default="sample_data/squad_eval_pack/golden_questions.final.jsonl",
        help="Path to output JSONL.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="top_k value for each question.",
    )
    args = parser.parse_args()

    mapping_path = Path(args.mapping)
    output_path = Path(args.output)

    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
    if args.top_k <= 0:
        raise ValueError("--top-k must be > 0")

    rows: list[dict] = []
    with mapping_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        required_fields = {
            "question_id",
            "question",
            "reference_doc",
            "expected_answer",
            "expected_chunk_ids_after_upload",
        }
        if not required_fields.issubset(set(reader.fieldnames or [])):
            missing = sorted(required_fields - set(reader.fieldnames or []))
            raise ValueError(f"Missing required columns in mapping CSV: {missing}")

        for line_number, row in enumerate(reader, start=2):
            question_id = (row.get("question_id") or "").strip()
            question = (row.get("question") or "").strip()
            reference_doc = (row.get("reference_doc") or "").strip()
            expected_answer = (row.get("expected_answer") or "").strip()
            expected_chunk_ids = parse_chunk_ids(row.get("expected_chunk_ids_after_upload") or "")

            if not question_id:
                raise ValueError(f"Line {line_number}: question_id is required")
            if not question:
                raise ValueError(f"Line {line_number}: question is required")
            if not expected_chunk_ids:
                raise ValueError(
                    f"Line {line_number}: expected_chunk_ids_after_upload is empty. "
                    "Please fill with chunk ids separated by '|'."
                )

            payload = {
                "id": question_id,
                "question": question,
                "expected_chunk_ids": expected_chunk_ids,
                "top_k": args.top_k,
                "notes": (
                    f"ref_doc={reference_doc}; "
                    f"expected_answer={expected_answer}"
                ),
            }
            rows.append(payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as jsonl_file:
        for row in rows:
            jsonl_file.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("DONE")
    print(f"Output JSONL: {output_path}")
    print(f"Questions: {len(rows)}")


if __name__ == "__main__":
    main()
