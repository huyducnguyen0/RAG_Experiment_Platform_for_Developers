from app.schemas.research import ResearchQueryResponse, ResearchSource
from app.services.ai_service import generate_mock_answer
from app.services.retrieval_service import retrieve_relevant_chunks

SOURCE_PREVIEW_LENGTH = 180


def answer_research_query(
    question: str,
    top_k: int = 3,
    workspace_id: str | None = None,
) -> ResearchQueryResponse:
    retrieval = retrieve_relevant_chunks(
        question=question,
        top_k=top_k,
        workspace_id=workspace_id,
    )
    sources = [
        _to_source(result)
        for result in retrieval.results
    ]
    context = _build_context(sources)
    answer = generate_mock_answer(question=question, context=context)

    return ResearchQueryResponse(
        answer=answer,
        sources=sources,
        mode="rag_mock",
    )


def _build_context(sources: list[ResearchSource]) -> str:
    return "\n\n".join(
        f"[{index}] {source.preview}"
        for index, source in enumerate(sources, start=1)
    )


def _to_source(result) -> ResearchSource:
    return ResearchSource(
        document_id=result.document_id,
        document_title=result.document_title,
        chunk_id=result.chunk_id,
        chunk_index=result.chunk_index,
        score=result.score,
        preview=_preview(result.content),
    )


def _preview(content: str) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= SOURCE_PREVIEW_LENGTH:
        return normalized

    return f"{normalized[:SOURCE_PREVIEW_LENGTH].rstrip()}..."
