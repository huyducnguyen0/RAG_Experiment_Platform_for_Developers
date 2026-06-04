import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.schemas.document import DocumentChunk, DocumentDetail, DocumentSummary, FolderUploadResponse
from app.services.chunking_service import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP, chunk_text

DATA_DIR = Path("data")
DOCUMENTS_DIR = DATA_DIR / "documents"
METADATA_PATH = DATA_DIR / "metadata.json"
WORKSPACES_DIR = DATA_DIR / "workspaces"
ALLOWED_EXTENSIONS = {".txt", ".md"}


def save_uploaded_document(
    file: UploadFile,
    workspace_id: str | None = None,
    relative_path: str | None = None,
) -> DocumentDetail:
    source_path = _normalize_relative_path(relative_path or file.filename)
    file_name = _safe_file_name(source_path)
    file_type = _validate_file_type(file_name)
    content = _read_text_file(file)
    return _save_document_content(
        workspace_id=workspace_id,
        file_name=file_name,
        file_type=file_type,
        content=content,
        source_path=source_path,
    )


def save_uploaded_folder_documents(
    files: list[UploadFile],
    relative_paths: list[str],
    workspace_id: str,
) -> FolderUploadResponse:
    imported_documents: list[DocumentDetail] = []
    skipped = 0

    for index, file in enumerate(files):
        relative_path = relative_paths[index] if index < len(relative_paths) else file.filename
        source_path = _normalize_relative_path(relative_path or file.filename)
        file_name = _safe_file_name(source_path)
        suffix = Path(file_name).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            skipped += 1
            continue

        try:
            file_type = _validate_file_type(file_name)
            content = _read_text_file(file)
        except HTTPException:
            skipped += 1
            continue

        imported_documents.append(
            _save_document_content(
                workspace_id=workspace_id,
                file_name=file_name,
                file_type=file_type,
                content=content,
                source_path=source_path,
            )
        )

    return FolderUploadResponse(
        workspace_id=workspace_id,
        imported=len(imported_documents),
        skipped=skipped,
        documents=[_to_summary(item.model_dump()) for item in imported_documents],
    )


def _save_document_content(
    workspace_id: str | None,
    file_name: str,
    file_type: str,
    content: str,
    source_path: str,
) -> DocumentDetail:
    corpus_metadata = _infer_corpus_metadata(source_path, file_type)

    document_id = f"doc_{uuid4().hex[:12]}"
    stored_file_name = f"{document_id}_{file_name}"
    documents_dir, _metadata_path = _get_storage_paths(workspace_id)
    stored_path = documents_dir / stored_file_name

    _ensure_storage(workspace_id)
    stored_path.write_text(content, encoding="utf-8")
    chunks = _attach_chunk_metadata(
        chunks=chunk_text(document_id, content),
        source_metadata=corpus_metadata,
        chunking_strategy="fixed",
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_OVERLAP,
    )

    metadata = {
        "id": document_id,
        "workspace_id": workspace_id,
        "title": file_name,
        "file_name": file_name,
        "file_type": file_type,
        **corpus_metadata,
        "content_length": len(content),
        "chunk_count": len(chunks),
        "chunks": [chunk.model_dump() for chunk in chunks],
        "created_at": datetime.now(UTC).isoformat(),
        "stored_file_name": stored_file_name,
    }

    all_metadata = _load_metadata(workspace_id)
    all_metadata.append(metadata)
    _save_metadata(all_metadata, workspace_id)

    return _to_detail(metadata, content)


def list_documents(workspace_id: str | None = None) -> list[DocumentSummary]:
    return [_to_summary(item) for item in _load_metadata(workspace_id)]


def get_document(
    document_id: str,
    workspace_id: str | None = None,
) -> DocumentDetail:
    metadata = _find_metadata(document_id, workspace_id)
    content = _read_document_content(metadata, workspace_id)
    return _to_detail(metadata, content)


def delete_document(
    document_id: str,
    workspace_id: str | None = None,
) -> None:
    all_metadata = _load_metadata(workspace_id)
    metadata = next((item for item in all_metadata if item["id"] == document_id), None)

    if metadata is None:
        raise HTTPException(status_code=404, detail="Document not found")

    documents_dir, _metadata_path = _get_storage_paths(workspace_id)
    stored_path = documents_dir / metadata["stored_file_name"]
    if stored_path.exists():
        stored_path.unlink()

    remaining_metadata = [
        item for item in all_metadata if item["id"] != document_id
    ]
    _save_metadata(remaining_metadata, workspace_id)


def _ensure_storage(workspace_id: str | None = None) -> None:
    documents_dir, metadata_path = _get_storage_paths(workspace_id)
    documents_dir.mkdir(parents=True, exist_ok=True)
    if not metadata_path.exists():
        metadata_path.write_text("[]", encoding="utf-8")


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


def _normalize_relative_path(path_value: str | None) -> str:
    if not path_value:
        raise HTTPException(status_code=400, detail="Missing file path")

    normalized = path_value.replace("\\", "/").strip().strip("/")
    parts = [
        part
        for part in normalized.split("/")
        if part and part not in {".", ".."}
    ]
    if not parts:
        raise HTTPException(status_code=400, detail="Missing file path")
    return "/".join(parts)


def _infer_corpus_metadata(source_path: str, file_type: str) -> dict:
    normalized_parts = source_path.split("/")
    folder_parts = normalized_parts[:-1]
    folder_path = "/".join(folder_parts)
    doc_type = folder_parts[0] if folder_parts else "root"

    return {
        "source_path": source_path,
        "relative_path": source_path,
        "folder_path": folder_path,
        "doc_type": doc_type,
        "file_extension": f".{file_type}",
    }


def _attach_chunk_metadata(
    chunks: list[DocumentChunk],
    source_metadata: dict,
    chunking_strategy: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[DocumentChunk]:
    return [
        chunk.model_copy(
            update={
                "original_text": chunk.original_text or chunk.content,
                "headline": chunk.headline or _infer_chunk_headline(chunk.content),
                "summary": chunk.summary,
                "source_path": source_metadata["source_path"],
                "relative_path": source_metadata["relative_path"],
                "folder_path": source_metadata["folder_path"],
                "doc_type": source_metadata["doc_type"],
                "file_extension": source_metadata["file_extension"],
                "chunking_strategy": chunking_strategy,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            }
        )
        for chunk in chunks
    ]


def _infer_chunk_headline(content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip().strip("#").strip()
        if stripped:
            return stripped[:120]
    return ""


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


def _load_metadata(workspace_id: str | None = None) -> list[dict]:
    _ensure_storage(workspace_id)
    _documents_dir, metadata_path = _get_storage_paths(workspace_id)
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def _save_metadata(
    metadata: list[dict],
    workspace_id: str | None = None,
) -> None:
    _ensure_storage(workspace_id)
    _documents_dir, metadata_path = _get_storage_paths(workspace_id)
    metadata_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )


def _find_metadata(
    document_id: str,
    workspace_id: str | None = None,
) -> dict:
    metadata = next(
        (item for item in _load_metadata(workspace_id) if item["id"] == document_id),
        None,
    )

    if metadata is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return metadata


def _read_document_content(
    metadata: dict,
    workspace_id: str | None = None,
) -> str:
    documents_dir, _metadata_path = _get_storage_paths(workspace_id)
    stored_path = documents_dir / metadata["stored_file_name"]
    if not stored_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found")

    return stored_path.read_text(encoding="utf-8")


def _get_storage_paths(workspace_id: str | None = None) -> tuple[Path, Path]:
    if workspace_id is None:
        return DOCUMENTS_DIR, METADATA_PATH

    workspace_dir = WORKSPACES_DIR / workspace_id
    return workspace_dir / "documents", workspace_dir / "metadata.json"


def _to_summary(metadata: dict) -> DocumentSummary:
    return DocumentSummary(
        id=metadata["id"],
        workspace_id=metadata.get("workspace_id"),
        title=metadata["title"],
        file_name=metadata["file_name"],
        file_type=metadata["file_type"],
        source_path=metadata.get("source_path", metadata["file_name"]),
        relative_path=metadata.get("relative_path", metadata["file_name"]),
        folder_path=metadata.get("folder_path", ""),
        doc_type=metadata.get("doc_type", "root"),
        file_extension=metadata.get("file_extension", f".{metadata['file_type']}"),
        content_length=metadata["content_length"],
        chunk_count=metadata.get("chunk_count", len(metadata.get("chunks", []))),
        created_at=metadata["created_at"],
    )


def _to_detail(metadata: dict, content: str) -> DocumentDetail:
    chunks = [
        DocumentChunk(**chunk)
        for chunk in metadata.get("chunks", [])
    ]

    return DocumentDetail(
        **_to_summary(metadata).model_dump(),
        content=content,
        chunks=chunks,
    )
