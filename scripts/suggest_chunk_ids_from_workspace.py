from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


WORKSPACES_DIR = Path("data/workspaces")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Suggest expected_chunk_ids for golden question mapping rows "
            "using uploaded workspace documents."
        ),
    )
    parser.add_argument(
        "--workspace-id",
        required=True,
        help="Workspace id that already contains uploaded documents.",
    )
    parser.add_argument(
        "--mapping",
        default="sample_data/squad_eval_pack/golden_questions_mapping.csv",
        help="Input mapping CSV path.",
    )
    parser.add_argument(
        "--output",
        default="sample_data/squad_eval_pack/golden_questions_mapping.suggested.csv",
        help="Output CSV path with suggestions.",
    )
    return parser.parse_args()


def normalize_text(value: str) -> str:
    lowered = value.casefold()
    cleaned = re.sub(r"\s+", " ", lowered)
    return cleaned.strip()


def load_workspace_documents(workspace_id: str) -> dict[str, dict]:
    metadata_path = WORKSPACES_DIR / workspace_id / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Workspace metadata not found: {metadata_path}")

    documents = json.loads(metadata_path.read_text(encoding="utf-8"))
    latest_by_file_name: dict[str, dict] = {}

    for document in documents:
        file_name = str(document.get("file_name", "")).strip()
        if not file_name:
            continue

        existing = latest_by_file_name.get(file_name)
        if existing is None or str(document.get("created_at", "")) > str(existing.get("created_at", "")):
            latest_by_file_name[file_name] = document

    if not latest_by_file_name:
        raise ValueError(f"No documents found in workspace: {workspace_id}")

    return latest_by_file_name


def find_matching_chunks(document: dict, expected_answer: str) -> list[str]:
    normalized_answer = normalize_text(expected_answer)
    if not normalized_answer:
        return []

    exact_matches: list[str] = []
    scored_matches: list[tuple[int, str]] = []
    answer_tokens = [token for token in re.findall(r"[a-zA-Z0-9]+", normalized_answer) if len(token) >= 3]

    for chunk in document.get("chunks", []):
        chunk_content = str(chunk.get("content", ""))
        normalized_chunk = normalize_text(chunk_content)
        chunk_id = str(chunk.get("chunk_id", "")).strip()
        if not chunk_id:
            continue

        if normalized_answer in normalized_chunk:
            exact_matches.append(chunk_id)
            continue

        overlap_score = sum(1 for token in answer_tokens if token in normalized_chunk)
        if overlap_score > 0:
            scored_matches.append((overlap_score, chunk_id))

    if exact_matches:
        return exact_matches

    if not scored_matches:
        return []

    scored_matches.sort(reverse=True)
    best_score = scored_matches[0][0]
    return [chunk_id for score, chunk_id in scored_matches if score == best_score]


def suggest_row(row: dict, documents_by_file_name: dict[str, dict]) -> dict:
    output = dict(row)
    question_id = str(row.get("question_id", "")).strip()
    reference_doc = str(row.get("reference_doc", "")).strip()
    expected_answer = str(row.get("expected_answer", "")).strip()
    current_chunk_ids = str(row.get("expected_chunk_ids_after_upload", "")).strip()

    output["matched_document_id"] = ""
    output["matched_document_title"] = ""
    output["suggested_chunk_ids"] = ""
    output["suggestion_status"] = ""

    if current_chunk_ids:
        output["suggestion_status"] = "kept_existing_value"
        output["suggested_chunk_ids"] = current_chunk_ids
        return output

    document = documents_by_file_name.get(reference_doc)
    if document is None:
        output["suggestion_status"] = "reference_doc_not_found"
        return output

    output["matched_document_id"] = str(document.get("id", ""))
    output["matched_document_title"] = str(document.get("title", ""))

    matched_chunk_ids = find_matching_chunks(document, expected_answer)
    if not matched_chunk_ids:
        output["suggestion_status"] = "no_chunk_match"
        return output

    joined_chunk_ids = "|".join(matched_chunk_ids)
    output["expected_chunk_ids_after_upload"] = joined_chunk_ids
    output["suggested_chunk_ids"] = joined_chunk_ids
    output["suggestion_status"] = (
        "single_exact_match" if len(matched_chunk_ids) == 1 else "multiple_candidate_chunks"
    )

    if not question_id:
        output["suggestion_status"] = "missing_question_id"

    return output


def main() -> None:
    args = parse_args()
    mapping_path = Path(args.mapping)
    output_path = Path(args.output)

    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping CSV not found: {mapping_path}")

    documents_by_file_name = load_workspace_documents(args.workspace_id)

    with mapping_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        input_rows = list(reader)
        if not input_rows:
            raise ValueError("Mapping CSV is empty")

        output_rows = [suggest_row(row, documents_by_file_name) for row in input_rows]

    fieldnames = list(input_rows[0].keys())
    extra_fields = [
        "matched_document_id",
        "matched_document_title",
        "suggested_chunk_ids",
        "suggestion_status",
    ]
    for field_name in extra_fields:
        if field_name not in fieldnames:
            fieldnames.append(field_name)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    status_counts: dict[str, int] = {}
    for row in output_rows:
        status = str(row.get("suggestion_status", "")).strip() or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1

    print("DONE")
    print(f"Workspace: {args.workspace_id}")
    print(f"Input mapping: {mapping_path}")
    print(f"Output mapping: {output_path}")
    print(f"Documents indexed: {len(documents_by_file_name)}")
    print(f"Rows processed: {len(output_rows)}")
    for status, count in sorted(status_counts.items()):
        print(f"- {status}: {count}")


if __name__ == "__main__":
    main()
