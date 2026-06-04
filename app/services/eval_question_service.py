import csv
import json
import re
from io import StringIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.schemas.eval import EvalQuestion
from app.services.document_service import WORKSPACES_DIR, _load_metadata


def upload_eval_questions_file(workspace_id: str, upload_file: UploadFile) -> int:
    file_name = (upload_file.filename or "").lower()
    if not file_name.endswith((".jsonl", ".csv")):
        raise HTTPException(status_code=400, detail="Only .jsonl and .csv files are supported")

    raw_bytes = upload_file.file.read()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded") from error

    parsed_questions = _parse_eval_questions(raw_text, workspace_id, file_name=file_name)
    if not parsed_questions:
        raise HTTPException(status_code=400, detail="No valid questions found in file")

    _save_workspace_questions(workspace_id, parsed_questions)
    return len(parsed_questions)


def list_eval_questions(workspace_id: str) -> list[EvalQuestion]:
    payloads = _load_workspace_questions(workspace_id)
    return [EvalQuestion(**item) for item in payloads]


def delete_eval_question(workspace_id: str, question_id: str) -> None:
    items = _load_workspace_questions(workspace_id)
    kept_items = [item for item in items if item["id"] != question_id]
    if len(kept_items) == len(items):
        raise HTTPException(status_code=404, detail="Evaluation question not found")
    _save_workspace_questions(workspace_id, kept_items)


def repair_eval_questions_missing_chunk_ids(workspace_id: str) -> int:
    items = _load_workspace_questions(workspace_id)
    if not items:
        return 0

    validation_context = _load_validation_context(workspace_id)
    repaired_count = 0
    repaired_items: list[dict] = []

    for item in items:
        expected_chunk_ids = [
            str(chunk_id).strip()
            for chunk_id in item.get("expected_chunk_ids", [])
            if str(chunk_id).strip()
        ]

        if expected_chunk_ids:
            repaired_items.append(
                {
                    **item,
                    "expected_chunk_ids": expected_chunk_ids,
                    "label_type": _determine_label_type(
                        expected_chunk_ids=expected_chunk_ids,
                        gold_evidence_text=str(item.get("gold_evidence_text", "")),
                        reference_answer=str(item.get("reference_answer", "")),
                        keywords=_normalize_keywords(item.get("keywords", [])),
                    ),
                }
            )
            continue

        inferred_chunk_ids = _infer_chunk_ids_from_notes(
            notes=str(item.get("notes", "")),
            validation_context=validation_context,
        )
        if inferred_chunk_ids:
            repaired_count += 1
            repaired_items.append(
                {
                    **item,
                    "expected_chunk_ids": inferred_chunk_ids,
                    "label_type": "strong_chunk_ids",
                }
            )
            continue

        repaired_items.append(item)

    if repaired_count > 0:
        _save_workspace_questions(workspace_id, repaired_items)

    return repaired_count


def _parse_eval_questions(raw_text: str, workspace_id: str, file_name: str) -> list[dict]:
    if file_name.endswith(".csv"):
        return _parse_csv_questions(raw_text, workspace_id)
    return _parse_jsonl_questions(raw_text, workspace_id)


def _parse_jsonl_questions(raw_text: str, workspace_id: str) -> list[dict]:
    parsed: list[dict] = []
    validation_context = _load_validation_context(workspace_id)

    for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON at line {line_number}",
            ) from error

        parsed.append(
            _normalize_eval_payload(
                payload=payload,
                workspace_id=workspace_id,
                line_number=line_number,
                validation_context=validation_context,
            )
        )

    return parsed


def _parse_csv_questions(raw_text: str, workspace_id: str) -> list[dict]:
    parsed: list[dict] = []
    validation_context = _load_validation_context(workspace_id)
    reader = csv.DictReader(StringIO(raw_text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file must include a header row")

    for line_number, row in enumerate(reader, start=2):
        payload = {str(key or "").strip(): value for key, value in row.items()}
        if not any(str(value or "").strip() for value in payload.values()):
            continue
        parsed.append(
            _normalize_eval_payload(
                payload=payload,
                workspace_id=workspace_id,
                line_number=line_number,
                validation_context=validation_context,
            )
        )

    return parsed


def _workspace_eval_file(workspace_id: str) -> Path:
    eval_dir = WORKSPACES_DIR / workspace_id / "eval_sets"
    eval_dir.mkdir(parents=True, exist_ok=True)
    return eval_dir / "golden_questions.jsonl"


def _load_workspace_questions(workspace_id: str) -> list[dict]:
    eval_file = _workspace_eval_file(workspace_id)
    if not eval_file.exists():
        return []

    questions: list[dict] = []
    for line in eval_file.read_text(encoding="utf-8").splitlines():
        content = line.strip()
        if not content:
            continue
        questions.append(json.loads(content))

    return questions


def _save_workspace_questions(workspace_id: str, items: list[dict]) -> None:
    eval_file = _workspace_eval_file(workspace_id)
    if not items:
        eval_file.write_text("", encoding="utf-8")
        return

    lines = [json.dumps(item, ensure_ascii=False) for item in items]
    eval_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_validation_context(workspace_id: str) -> dict:
    documents = _load_metadata(workspace_id)
    chunk_ids: set[str] = set()
    latest_documents_by_file_name: dict[str, dict] = {}

    for document in documents:
        file_name = str(document.get("file_name", "")).strip()
        if file_name:
            existing = latest_documents_by_file_name.get(file_name)
            if existing is None or str(document.get("created_at", "")) > str(existing.get("created_at", "")):
                latest_documents_by_file_name[file_name] = document

        for chunk in document.get("chunks", []):
            chunk_id = str(chunk.get("chunk_id", "")).strip()
            if chunk_id:
                chunk_ids.add(chunk_id)

    return {
        "chunk_ids": chunk_ids,
        "latest_documents_by_file_name": latest_documents_by_file_name,
    }


def _normalize_eval_payload(
    payload: dict,
    workspace_id: str,
    line_number: int,
    validation_context: dict,
) -> dict:
    question = str(payload.get("question", "")).strip()
    if not question:
        raise HTTPException(status_code=400, detail=f"Line {line_number}: question is required")

    top_k = _parse_top_k(payload.get("top_k", 5), line_number)
    notes = str(payload.get("notes", "")).strip()
    question_id = (
        str(payload.get("id", "")).strip()
        or str(payload.get("q_id", "")).strip()
        or f"q_{uuid4().hex[:12]}"
    )
    reference_answer = str(payload.get("reference_answer", "")).strip()
    category = str(payload.get("category", "")).strip()
    gold_evidence_text = str(payload.get("gold_evidence_text", "")).strip()
    keywords = _normalize_keywords(payload.get("keywords", []))
    expected_chunk_ids = _resolve_expected_chunk_ids(
        expected_chunk_ids=payload.get("expected_chunk_ids", []),
        notes=notes,
        line_number=line_number,
        validation_context=validation_context,
        allow_empty=True,
    )

    if not expected_chunk_ids and not gold_evidence_text and not reference_answer and not keywords:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Line {line_number}: provide at least one supervision field: "
                "expected_chunk_ids, gold_evidence_text, reference_answer, or keywords"
            ),
        )

    valid_chunk_ids = validation_context["chunk_ids"]
    unknown_chunk_ids = sorted(set(expected_chunk_ids) - valid_chunk_ids)
    if unknown_chunk_ids and valid_chunk_ids:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Line {line_number}: unknown chunk ids for workspace {workspace_id}: "
                f"{', '.join(unknown_chunk_ids)}"
            ),
        )

    return {
        "id": question_id,
        "workspace_id": workspace_id,
        "question": question,
        "expected_chunk_ids": expected_chunk_ids,
        "reference_answer": reference_answer,
        "keywords": keywords,
        "category": category,
        "gold_evidence_text": gold_evidence_text,
        "label_type": _determine_label_type(
            expected_chunk_ids=expected_chunk_ids,
            gold_evidence_text=gold_evidence_text,
            reference_answer=reference_answer,
            keywords=keywords,
        ),
        "top_k": top_k,
        "notes": notes,
    }


def _parse_top_k(raw_value: object, line_number: int) -> int:
    try:
        top_k = int(raw_value)
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=f"Line {line_number}: top_k must be an integer") from error
    if top_k <= 0:
        raise HTTPException(status_code=400, detail=f"Line {line_number}: top_k must be > 0")
    return top_k


def _normalize_keywords(raw_keywords: object) -> list[str]:
    if isinstance(raw_keywords, list):
        return [str(item).strip() for item in raw_keywords if str(item).strip()]
    if isinstance(raw_keywords, str):
        normalized = raw_keywords.strip()
        if not normalized:
            return []
        parts = re.split(r"[;,|\n]", normalized)
        return [part.strip() for part in parts if part.strip()]
    if raw_keywords is None:
        return []
    normalized = str(raw_keywords).strip()
    return [normalized] if normalized else []


def _determine_label_type(
    expected_chunk_ids: list[str],
    gold_evidence_text: str,
    reference_answer: str,
    keywords: list[str],
) -> str:
    if expected_chunk_ids:
        return "strong_chunk_ids"
    if gold_evidence_text.strip():
        return "evidence_text"
    if reference_answer.strip() or keywords:
        return "weak_label"
    return "question_only"


def _resolve_expected_chunk_ids(
    expected_chunk_ids: list,
    notes: str,
    line_number: int,
    validation_context: dict,
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(expected_chunk_ids, list):
        raise HTTPException(
            status_code=400,
            detail=f"Line {line_number}: expected_chunk_ids must be a list",
        )

    normalized_chunk_ids = [
        str(item).strip()
        for item in expected_chunk_ids
        if str(item).strip()
    ]

    if normalized_chunk_ids:
        return normalized_chunk_ids

    inferred_chunk_ids = _infer_chunk_ids_from_notes(
        notes=notes,
        validation_context=validation_context,
    )
    if inferred_chunk_ids:
        return inferred_chunk_ids

    if allow_empty:
        return []

    raise HTTPException(
        status_code=400,
        detail=(
            f"Line {line_number}: expected_chunk_ids is empty and could not be inferred. "
            "Use notes like 'ref_doc=<file_name>; expected_answer=<answer>' or provide chunk ids explicitly."
        ),
    )


def _infer_chunk_ids_from_notes(notes: str, validation_context: dict) -> list[str]:
    reference_doc = _extract_note_value(notes, "ref_doc")
    expected_answer = _extract_note_value(notes, "expected_answer")
    if not reference_doc or not expected_answer:
        return []

    document = validation_context["latest_documents_by_file_name"].get(reference_doc)
    if document is None:
        return []

    return _find_matching_chunk_ids(
        document=document,
        expected_answer=expected_answer,
    )


def _extract_note_value(notes: str, key: str) -> str:
    match = re.search(rf"(?:^|;\s*){re.escape(key)}=([^;]+)", notes)
    if not match:
        return ""

    return match.group(1).strip()


def _find_matching_chunk_ids(document: dict, expected_answer: str) -> list[str]:
    normalized_answer = _normalize_text(expected_answer)
    if not normalized_answer:
        return []

    exact_matches: list[str] = []
    scored_matches: list[tuple[int, str]] = []
    answer_tokens = [
        token
        for token in re.findall(r"[a-zA-Z0-9]+", normalized_answer)
        if len(token) >= 3
    ]

    for chunk in document.get("chunks", []):
        chunk_id = str(chunk.get("chunk_id", "")).strip()
        normalized_chunk = _normalize_text(str(chunk.get("content", "")))
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


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()
