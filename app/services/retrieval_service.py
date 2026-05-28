import re

from app.schemas.research import RetrievedChunk, RetrieveResponse
from app.services.document_service import _load_metadata

MIN_KEYWORD_LENGTH = 2


def retrieve_relevant_chunks(question: str, top_k: int = 3) -> RetrieveResponse:
    keywords = _extract_keywords(question)
    results: list[RetrievedChunk] = []

    if not keywords:
        return RetrieveResponse(query=question, results=[])

    for document in _load_metadata():
        for chunk in document.get("chunks", []):
            score = _score_chunk(chunk["content"], keywords)
            if score <= 0:
                continue

            results.append(
                RetrievedChunk(
                    document_id=document["id"],
                    document_title=document["title"],
                    chunk_id=chunk["chunk_id"],
                    chunk_index=chunk["chunk_index"],
                    score=score,
                    content=chunk["content"],
                )
            )

    ranked_results = sorted(
        results,
        key=lambda result: (result.score, -result.chunk_index),
        reverse=True,
    )

    return RetrieveResponse(query=question, results=ranked_results[:top_k])


def _extract_keywords(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [
        word
        for word in words
        if len(word) >= MIN_KEYWORD_LENGTH
    ]


def _score_chunk(content: str, keywords: list[str]) -> int:
    normalized_content = content.lower()
    return sum(
        normalized_content.count(keyword)
        for keyword in keywords
    )
