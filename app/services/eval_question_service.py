import json
import re
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.schemas.eval import EvalQuestion
from app.services.document_service import WORKSPACES_DIR, _load_metadata


def upload_eval_questions_file(workspace_id: str, upload_file: UploadFile) -> int:
    file_name = (upload_file.filename or "").lower()
    if not file_name.endswith(".jsonl"):
        raise HTTPException(status_code=400, detail="Only .jsonl files are supported")

    raw_bytes = upload_file.file.read()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded") from error

    parsed_questions = _parse_jsonl_questions(raw_text, workspace_id)
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
            repaired_items.append({**item, "expected_chunk_ids": expected_chunk_ids})
            continue

        inferred_chunk_ids = _infer_chunk_ids_from_notes(
            notes=str(item.get("notes", "")),
            validation_context=validation_context,
        )
        if inferred_chunk_ids:
            repaired_count += 1
            repaired_items.append({**item, "expected_chunk_ids": inferred_chunk_ids})
            continue

        repaired_items.append(item)

    if repaired_count > 0:
        _save_workspace_questions(workspace_id, repaired_items)

    return repaired_count


def _parse_jsonl_questions(raw_text: str, workspace_id: str) -> list[dict]:
    parsed: list[dict] = []
    validation_context = _load_validation_context(workspace_id)
    valid_chunk_ids = validation_context["chunk_ids"]

    if not valid_chunk_ids:
        raise HTTPException(
            status_code=400,
            detail=(
                "This workspace has no document chunks yet. "
                "Upload documents before uploading golden questions."
            ),
        )

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

        question = str(payload.get("question", "")).strip()
        expected_chunk_ids = payload.get("expected_chunk_ids", [])
        top_k = int(payload.get("top_k", 3))
        notes = str(payload.get("notes", ""))
        question_id = str(payload.get("id", "")).strip() or f"q_{uuid4().hex[:12]}"

        if not question:
            raise HTTPException(status_code=400, detail=f"Line {line_number}: question is required")
        if not isinstance(expected_chunk_ids, list):
            raise HTTPException(
                status_code=400,
                detail=f"Line {line_number}: expected_chunk_ids must be a list",
            )
        if top_k <= 0:
            raise HTTPException(status_code=400, detail=f"Line {line_number}: top_k must be > 0")

        normalized_chunk_ids = _resolve_expected_chunk_ids(
            expected_chunk_ids=expected_chunk_ids,
            notes=notes,
            line_number=line_number,
            validation_context=validation_context,
        )

        if not normalized_chunk_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Line {line_number}: expected_chunk_ids must contain at least one non-empty chunk id",
            )

        unknown_chunk_ids = sorted(set(normalized_chunk_ids) - valid_chunk_ids)
        if unknown_chunk_ids:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Line {line_number}: unknown chunk ids for workspace {workspace_id}: "
                    f"{', '.join(unknown_chunk_ids)}"
                ),
            )

        parsed.append(
            {
                "id": question_id,
                "workspace_id": workspace_id,
                "question": question,
                "expected_chunk_ids": normalized_chunk_ids,
                "top_k": top_k,
                "notes": notes,
            }
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


def _resolve_expected_chunk_ids(
    expected_chunk_ids: list,
    notes: str,
    line_number: int,
    validation_context: dict,
) -> list[str]:
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
