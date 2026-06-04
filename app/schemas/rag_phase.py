from pydantic import BaseModel


class RagPhase(BaseModel):
    phase_id: str
    name: str
    description: str
    status: str
    enabled: bool
    order: int


class RagPhaseListResponse(BaseModel):
    items: list[RagPhase]
    total: int
