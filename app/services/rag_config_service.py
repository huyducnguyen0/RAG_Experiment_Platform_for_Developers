from __future__ import annotations

from fastapi import HTTPException

from app.schemas.rag_config import RagConfigComponent, RagConfigPreset
from app.services.chunking_service import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP
from app.services.retrieval_service import SUPPORTED_RETRIEVAL_STRATEGIES

DEFAULT_RAG_STAGE = "retriever_evaluation"
CHUNKING_RAG_STAGE = "chunking_evaluation"
DEFAULT_TOP_K = 5


def list_rag_config_presets(workspace_id: str | None = None) -> list[RagConfigPreset]:
    _ = workspace_id
    return [
        _build_chunking_config(
            config_id="cfg_chunk_fixed_500_50",
            name="Chunk fixed 500 / overlap 50",
            description="Chunk documents into smaller 500-character windows with 50-character overlap.",
            chunk_size=500,
            overlap=50,
        ),
        _build_chunking_config(
            config_id="cfg_chunk_fixed_800_100",
            name="Chunk fixed 800 / overlap 100",
            description="Current default fixed chunking baseline.",
            chunk_size=800,
            overlap=100,
        ),
        _build_chunking_config(
            config_id="cfg_chunk_fixed_1200_150",
            name="Chunk fixed 1200 / overlap 150",
            description="Larger fixed chunks for longer context windows.",
            chunk_size=1200,
            overlap=150,
        ),
        _build_chunking_config(
            config_id="cfg_chunk_paragraph_1000",
            name="Chunk paragraph max 1000",
            description="Group neighboring paragraphs up to roughly 1000 characters.",
            chunking_type="paragraph",
            max_chunk_size=1000,
        ),
        _build_chunking_config(
            config_id="cfg_chunk_recursive_500_200",
            name="Chunk recursive 500 / overlap 200",
            description="LangChain recursive character splitting with smaller chunks and larger overlap.",
            chunking_type="recursive_character",
            chunk_size=500,
            overlap=200,
        ),
        _build_chunking_config(
            config_id="cfg_chunk_recursive_800_200",
            name="Chunk recursive 800 / overlap 200",
            description="LangChain recursive character splitting with balanced chunk size.",
            chunking_type="recursive_character",
            chunk_size=800,
            overlap=200,
        ),
        _build_chunking_config(
            config_id="cfg_chunk_recursive_1000_250",
            name="Chunk recursive 1000 / overlap 250",
            description="LangChain recursive character splitting with larger context windows.",
            chunking_type="recursive_character",
            chunk_size=1000,
            overlap=250,
        ),
        _build_retriever_config(
            config_id="cfg_keyword_baseline",
            name="Keyword baseline",
            description="Lexical baseline using simple keyword matching.",
            strategy="keyword",
        ),
        _build_retriever_config(
            config_id="cfg_vector_default",
            name="Vector semantic retrieval",
            description="Semantic retrieval using local embeddings and Chroma.",
            strategy="vector",
        ),
        _build_retriever_config(
            config_id="cfg_hybrid_default",
            name="Hybrid keyword + vector",
            description="Combined lexical and semantic retrieval baseline.",
            strategy="hybrid",
        ),
    ]


def get_rag_config_preset(config_id: str, workspace_id: str | None = None) -> RagConfigPreset:
    selected_config_id = config_id.strip().lower()
    for preset in list_rag_config_presets(workspace_id=workspace_id):
        if preset.config_id == selected_config_id:
            return preset

    allowed = ", ".join(preset.config_id for preset in list_rag_config_presets(workspace_id=workspace_id))
    raise HTTPException(status_code=400, detail=f"Unsupported rag_config id. Allowed: {allowed}")


def get_rag_config_by_strategy(strategy: str, workspace_id: str | None = None) -> RagConfigPreset:
    selected_strategy = strategy.strip().lower()
    for preset in list_rag_config_presets(workspace_id=workspace_id):
        if preset.strategy == selected_strategy and preset.rag_stage == DEFAULT_RAG_STAGE:
            return preset

    for preset in list_rag_config_presets(workspace_id=workspace_id):
        if preset.strategy == selected_strategy:
            return preset

    allowed = ", ".join(sorted(SUPPORTED_RETRIEVAL_STRATEGIES))
    raise HTTPException(status_code=400, detail=f"Unsupported strategy. Allowed: {allowed}")


def resolve_rag_config_identifiers(
    config_ids: list[str] | None,
    strategies: list[str],
    workspace_id: str | None = None,
) -> list[RagConfigPreset]:
    if config_ids:
        presets = [
            get_rag_config_preset(config_id=config_id, workspace_id=workspace_id)
            for config_id in config_ids
            if config_id.strip()
        ]
    else:
        presets = [
            get_rag_config_by_strategy(strategy=strategy, workspace_id=workspace_id)
            for strategy in strategies
            if strategy.strip()
        ]

    deduped: list[RagConfigPreset] = []
    seen_config_ids: set[str] = set()
    for preset in presets:
        if preset.config_id not in seen_config_ids:
            deduped.append(preset)
            seen_config_ids.add(preset.config_id)

    if not deduped:
        raise HTTPException(status_code=400, detail="At least one rag_config is required")

    return deduped


def _build_retriever_config(
    config_id: str,
    name: str,
    description: str,
    strategy: str,
) -> RagConfigPreset:
    return RagConfigPreset(
        config_id=config_id,
        name=name,
        description=description,
        rag_stage=DEFAULT_RAG_STAGE,
        strategy=strategy,
        top_k=DEFAULT_TOP_K,
        chunking=RagConfigComponent(
            type="fixed",
            params={
                "chunk_size": DEFAULT_CHUNK_SIZE,
                "overlap": DEFAULT_OVERLAP,
            },
        ),
        retriever=RagConfigComponent(
            type=strategy,
            params={
                "top_k": DEFAULT_TOP_K,
            },
        ),
        query_transform=RagConfigComponent(type="none"),
        reranker=RagConfigComponent(type="none"),
        context_builder=RagConfigComponent(type="plain_top_k"),
    )


def _build_chunking_config(
    config_id: str,
    name: str,
    description: str,
    chunking_type: str = "fixed",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    max_chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> RagConfigPreset:
    chunking_params: dict[str, str | int | float | bool]
    if chunking_type == "paragraph":
        chunking_params = {"max_chunk_size": max_chunk_size}
    else:
        chunking_params = {
            "chunk_size": chunk_size,
            "overlap": overlap,
        }

    return RagConfigPreset(
        config_id=config_id,
        name=name,
        description=description,
        rag_stage=CHUNKING_RAG_STAGE,
        strategy="keyword",
        top_k=DEFAULT_TOP_K,
        chunking=RagConfigComponent(
            type=chunking_type,
            params=chunking_params,
        ),
        retriever=RagConfigComponent(
            type="keyword",
            params={
                "top_k": DEFAULT_TOP_K,
            },
        ),
        query_transform=RagConfigComponent(type="none"),
        reranker=RagConfigComponent(type="none"),
        context_builder=RagConfigComponent(type="plain_top_k"),
    )
