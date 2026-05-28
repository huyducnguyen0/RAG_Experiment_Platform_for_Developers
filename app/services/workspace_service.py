import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from app.schemas.workspace import WorkspaceDetail, WorkspaceSummary
from app.services.document_service import WORKSPACES_DIR, _load_metadata

WORKSPACE_INDEX_PATH = WORKSPACES_DIR / "metadata.json"


def create_workspace(name: str) -> WorkspaceDetail:
    clean_name = name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Workspace name is required")

    workspace_id = f"ws_{uuid4().hex[:12]}"
    workspace_dir = WORKSPACES_DIR / workspace_id
    workspace_dir.mkdir(parents=True, exist_ok=True)
    (workspace_dir / "documents").mkdir(parents=True, exist_ok=True)
    (workspace_dir / "metadata.json").write_text("[]", encoding="utf-8")

    metadata = {
        "id": workspace_id,
        "name": clean_name,
        "created_at": datetime.now(UTC).isoformat(),
    }

    workspaces = _load_workspace_index()
    workspaces.append(metadata)
    _save_workspace_index(workspaces)

    return _to_detail(metadata)


def list_workspaces() -> list[WorkspaceSummary]:
    return [_to_summary(item) for item in _load_workspace_index()]


def get_workspace(workspace_id: str) -> WorkspaceDetail:
    return _to_detail(_find_workspace(workspace_id))


def rename_workspace(workspace_id: str, name: str) -> WorkspaceDetail:
    clean_name = name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Workspace name is required")

    workspaces = _load_workspace_index()
    workspace = next(
        (item for item in workspaces if item["id"] == workspace_id),
        None,
    )

    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    workspace["name"] = clean_name
    _save_workspace_index(workspaces)

    return _to_detail(workspace)


def delete_workspace(workspace_id: str) -> None:
    workspace = _find_workspace(workspace_id)
    remaining = [
        item for item in _load_workspace_index() if item["id"] != workspace["id"]
    ]
    _save_workspace_index(remaining)

    workspace_dir = WORKSPACES_DIR / workspace_id
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)


def ensure_workspace_exists(workspace_id: str) -> None:
    _find_workspace(workspace_id)


def _ensure_workspace_index() -> None:
    WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)
    if not WORKSPACE_INDEX_PATH.exists():
        WORKSPACE_INDEX_PATH.write_text("[]", encoding="utf-8")


def _load_workspace_index() -> list[dict]:
    _ensure_workspace_index()
    return json.loads(WORKSPACE_INDEX_PATH.read_text(encoding="utf-8"))


def _save_workspace_index(workspaces: list[dict]) -> None:
    _ensure_workspace_index()
    WORKSPACE_INDEX_PATH.write_text(
        json.dumps(workspaces, indent=2),
        encoding="utf-8",
    )


def _find_workspace(workspace_id: str) -> dict:
    workspace = next(
        (item for item in _load_workspace_index() if item["id"] == workspace_id),
        None,
    )

    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return workspace


def _to_summary(metadata: dict) -> WorkspaceSummary:
    documents = _load_metadata(metadata["id"])
    return WorkspaceSummary(
        id=metadata["id"],
        name=metadata["name"],
        created_at=metadata["created_at"],
        document_count=len(documents),
    )


def _to_detail(metadata: dict) -> WorkspaceDetail:
    documents = _load_metadata(metadata["id"])
    return WorkspaceDetail(
        **_to_summary(metadata).model_dump(),
        document_ids=[document["id"] for document in documents],
    )
