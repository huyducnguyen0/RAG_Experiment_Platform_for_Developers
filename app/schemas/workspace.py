from pydantic import BaseModel


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceSummary(BaseModel):
    id: str
    name: str
    created_at: str
    document_count: int


class WorkspaceDetail(WorkspaceSummary):
    document_ids: list[str]


class DeleteWorkspaceResponse(BaseModel):
    deleted: bool
    workspace_id: str
