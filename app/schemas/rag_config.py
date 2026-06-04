from pydantic import BaseModel, Field


class RagConfigComponent(BaseModel):
    type: str
    params: dict[str, str | int | float | bool] = Field(default_factory=dict)


class RagConfigPreset(BaseModel):
    config_id: str
    name: str
    description: str
    rag_stage: str
    strategy: str
    top_k: int = 5
    chunking: RagConfigComponent
    retriever: RagConfigComponent
    query_transform: RagConfigComponent
    reranker: RagConfigComponent
    context_builder: RagConfigComponent
    answer_generator: RagConfigComponent


class RagConfigListResponse(BaseModel):
    items: list[RagConfigPreset]
    total: int
