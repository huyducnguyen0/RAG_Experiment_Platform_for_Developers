import json
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.schemas.eval import EvalQuestion
from app.services.document_service import WORKSPACES_DIR


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


def _parse_jsonl_questions(raw_text: str, workspace_id: str) -> list[dict]:
    parsed: list[dict] = []

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

        parsed.append(
            {
                "id": question_id,
                "workspace_id": workspace_id,
                "question": question,
                "expected_chunk_ids": [str(item) for item in expected_chunk_ids],
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
