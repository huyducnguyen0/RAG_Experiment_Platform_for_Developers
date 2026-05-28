import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.schemas.document import DocumentDetail, DocumentSummary

DATA_DIR = Path("data")
DOCUMENTS_DIR = DATA_DIR / "documents"
METADATA_PATH = DATA_DIR / "metadata.json"
ALLOWED_EXTENSIONS = {".txt", ".md"}


def save_uploaded_document(file: UploadFile) -> DocumentDetail:
    file_name = _safe_file_name(file.filename)
    file_type = _validate_file_type(file_name)
    content = _read_text_file(file)

    document_id = f"doc_{uuid4().hex[:12]}"
    stored_file_name = f"{document_id}_{file_name}"
    stored_path = DOCUMENTS_DIR / stored_file_name

    _ensure_storage()
    stored_path.write_text(content, encoding="utf-8")

    metadata = {
        "id": document_id,
        "title": file_name,
        "file_name": file_name,
        "file_type": file_type,
        "content_length": len(content),
        "created_at": datetime.now(UTC).isoformat(),
        "stored_file_name": stored_file_name,
    }

    all_metadata = _load_metadata()
    all_metadata.append(metadata)
    _save_metadata(all_metadata)

    return _to_detail(metadata, content)


def list_documents() -> list[DocumentSummary]:
    return [_to_summary(item) for item in _load_metadata()]


def get_document(document_id: str) -> DocumentDetail:
    metadata = _find_metadata(document_id)
    content = _read_document_content(metadata)
    return _to_detail(metadata, content)


def delete_document(document_id: str) -> None:
    all_metadata = _load_metadata()
    metadata = next((item for item in all_metadata if item["id"] == document_id), None)

    if metadata is None:
        raise HTTPException(status_code=404, detail="Document not found")

    stored_path = DOCUMENTS_DIR / metadata["stored_file_name"]
    if stored_path.exists():
        stored_path.unlink()

    remaining_metadata = [
        item for item in all_metadata if item["id"] != document_id
    ]
    _save_metadata(remaining_metadata)


def _ensure_storage() -> None:
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    if not METADATA_PATH.exists():
        METADATA_PATH.write_text("[]", encoding="utf-8")


def _safe_file_name(file_name: str | None) -> str:
    if not file_name:
        raise HTTPException(status_code=400, detail="Missing file name")

    return Path(file_name).name


def _validate_file_type(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .md files are supported",
        )

    return suffix.removeprefix(".")


def _read_text_file(file: UploadFile) -> str:
    raw_content = file.file.read()

    if not raw_content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        content = raw_content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail="File must be valid UTF-8 text",
        ) from error

    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    return content


def _load_metadata() -> list[dict]:
    _ensure_storage()
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


def _save_metadata(metadata: list[dict]) -> None:
    _ensure_storage()
    METADATA_PATH.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )


def _find_metadata(document_id: str) -> dict:
    metadata = next(
        (item for item in _load_metadata() if item["id"] == document_id),
        None,
    )

    if metadata is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return metadata


def _read_document_content(metadata: dict) -> str:
    stored_path = DOCUMENTS_DIR / metadata["stored_file_name"]
    if not stored_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found")

    return stored_path.read_text(encoding="utf-8")


def _to_summary(metadata: dict) -> DocumentSummary:
    return DocumentSummary(
        id=metadata["id"],
        title=metadata["title"],
        file_name=metadata["file_name"],
        file_type=metadata["file_type"],
        content_length=metadata["content_length"],
        created_at=metadata["created_at"],
    )


def _to_detail(metadata: dict, content: str) -> DocumentDetail:
    return DocumentDetail(
        **_to_summary(metadata).model_dump(),
        content=content,
    )
