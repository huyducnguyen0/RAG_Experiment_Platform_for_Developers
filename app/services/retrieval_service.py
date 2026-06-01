import hashlib
import re
from functools import lru_cache

from fastapi import HTTPException
from sentence_transformers import SentenceTransformer

from app.vectorstore.chroma_client import get_chroma_client
from app.schemas.research import RetrievedChunk, RetrieveResponse
from app.services.document_service import _load_metadata

MIN_KEYWORD_LENGTH = 2
SUPPORTED_RETRIEVAL_STRATEGIES = {"keyword", "vector", "hybrid"}
VECTOR_COLLECTION_PREFIX = "workspace_"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
_INDEXED_WORKSPACE_SIGNATURES: dict[str, str] = {}


def retrieve_relevant_chunks(
    question: str,
    top_k: int = 3,
    workspace_id: str | None = None,
    strategy: str = "keyword",
) -> RetrieveResponse:
    normalized_strategy = strategy.strip().lower()
    _validate_retrieval_strategy(normalized_strategy, original_strategy=strategy)

    if normalized_strategy == "vector":
        if workspace_id is None:
            raise HTTPException(
                status_code=400,
                detail="Vector retrieval requires workspace_id",
            )
        return _retrieve_relevant_chunks_vector(
            question=question,
            top_k=top_k,
            workspace_id=workspace_id,
        )
    if normalized_strategy == "hybrid":
        if workspace_id is None:
            raise HTTPException(
                status_code=400,
                detail="Hybrid retrieval requires workspace_id",
            )
        return _retrieve_relevant_chunks_hybrid(
            question=question,
            top_k=top_k,
            workspace_id=workspace_id,
        )

    return _retrieve_relevant_chunks_keyword(
        question=question,
        top_k=top_k,
        workspace_id=workspace_id,
    )


def prepare_retrieval_strategy(workspace_id: str, strategy: str) -> None:
    normalized_strategy = strategy.strip().lower()
    _validate_retrieval_strategy(normalized_strategy, original_strategy=strategy)

    if normalized_strategy not in {"vector", "hybrid"}:
        return

    chunks = _collect_workspace_chunks(workspace_id)
    if chunks:
        _upsert_workspace_collection(workspace_id, chunks)


def _validate_retrieval_strategy(normalized_strategy: str, original_strategy: str) -> None:
    if normalized_strategy not in SUPPORTED_RETRIEVAL_STRATEGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported retrieval strategy: {original_strategy}",
        )


def _retrieve_relevant_chunks_keyword(
    question: str,
    top_k: int = 3,
    workspace_id: str | None = None,
) -> RetrieveResponse:
    keywords = _extract_keywords(question)
    results: list[RetrievedChunk] = []

    if not keywords:
        return RetrieveResponse(query=question, results=[])

    for document in _load_metadata(workspace_id):
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
                    score=float(score),
                    content=chunk["content"],
                )
            )

    ranked_results = sorted(
        results,
        key=lambda result: (result.score, -result.chunk_index),
        reverse=True,
    )

    return RetrieveResponse(query=question, results=ranked_results[:top_k])


def _retrieve_relevant_chunks_vector(
    question: str,
    top_k: int,
    workspace_id: str,
) -> RetrieveResponse:
    question_text = question.strip()
    if not question_text:
        return RetrieveResponse(query=question, results=[])

    chunks = _collect_workspace_chunks(workspace_id)
    if not chunks:
        return RetrieveResponse(query=question, results=[])

    collection = _upsert_workspace_collection(workspace_id, chunks)
    question_embedding = _embedding_model().encode([question_text])[0].tolist()

    query_result = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(top_k, len(chunks)),
        include=["documents", "metadatas", "distances"],
    )

    ids = query_result.get("ids", [[]])[0]
    metadatas = query_result.get("metadatas", [[]])[0]
    documents = query_result.get("documents", [[]])[0]
    distances = query_result.get("distances", [[]])[0]
    results: list[RetrievedChunk] = []

    for chunk_id, metadata, content, distance in zip(ids, metadatas, documents, distances):
        similarity = float(1.0 / (1.0 + distance))
        results.append(
            RetrievedChunk(
                document_id=str(metadata.get("document_id", "")),
                document_title=str(metadata.get("document_title", "")),
                chunk_id=chunk_id,
                chunk_index=int(metadata.get("chunk_index", 0)),
                score=similarity,
                content=content,
            )
        )

    return RetrieveResponse(query=question, results=results)


def _retrieve_relevant_chunks_hybrid(
    question: str,
    top_k: int,
    workspace_id: str,
) -> RetrieveResponse:
    overfetch_k = max(top_k * 3, top_k)
    keyword_results = _retrieve_relevant_chunks_keyword(
        question=question,
        top_k=overfetch_k,
        workspace_id=workspace_id,
    ).results
    vector_results = _retrieve_relevant_chunks_vector(
        question=question,
        top_k=overfetch_k,
        workspace_id=workspace_id,
    ).results

    combined_results = _combine_ranked_results(
        keyword_results=keyword_results,
        vector_results=vector_results,
    )
    return RetrieveResponse(query=question, results=combined_results[:top_k])


def _combine_ranked_results(
    keyword_results: list[RetrievedChunk],
    vector_results: list[RetrievedChunk],
) -> list[RetrievedChunk]:
    by_chunk_id: dict[str, RetrievedChunk] = {}
    scores: dict[str, float] = {}

    for ranked_results in (keyword_results, vector_results):
        for rank, result in enumerate(ranked_results, start=1):
            by_chunk_id[result.chunk_id] = result
            scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + (1.0 / rank)

    ranked_chunk_ids = sorted(
        scores,
        key=lambda chunk_id: scores[chunk_id],
        reverse=True,
    )

    return [
        RetrievedChunk(
            document_id=by_chunk_id[chunk_id].document_id,
            document_title=by_chunk_id[chunk_id].document_title,
            chunk_id=by_chunk_id[chunk_id].chunk_id,
            chunk_index=by_chunk_id[chunk_id].chunk_index,
            score=scores[chunk_id],
            content=by_chunk_id[chunk_id].content,
        )
        for chunk_id in ranked_chunk_ids
    ]


def _collect_workspace_chunks(workspace_id: str) -> list[dict]:
    chunks: list[dict] = []
    for document in _load_metadata(workspace_id):
        for chunk in document.get("chunks", []):
            chunks.append(
                {
                    "document_id": document["id"],
                    "document_title": document["title"],
                    "chunk_id": chunk["chunk_id"],
                    "chunk_index": chunk["chunk_index"],
                    "content": chunk["content"],
                }
            )
    return chunks


def _upsert_workspace_collection(workspace_id: str, chunks: list[dict]):
    client = get_chroma_client()
    collection_name = _collection_name(workspace_id)
    chunks_signature = _workspace_chunks_signature(chunks)

    if _INDEXED_WORKSPACE_SIGNATURES.get(workspace_id) == chunks_signature:
        return client.get_or_create_collection(name=collection_name)

    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    collection = client.get_or_create_collection(name=collection_name)

    ids = [chunk["chunk_id"] for chunk in chunks]
    embeddings = _embedding_model().encode([chunk["content"] for chunk in chunks]).tolist()
    metadatas = [
        {
            "workspace_id": workspace_id,
            "document_id": chunk["document_id"],
            "document_title": chunk["document_title"],
            "chunk_index": chunk["chunk_index"],
        }
        for chunk in chunks
    ]
    documents = [chunk["content"] for chunk in chunks]

    try:
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )
        _INDEXED_WORKSPACE_SIGNATURES[workspace_id] = chunks_signature
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Vector index upsert failed: {error}",
        ) from error

    return collection


@lru_cache(maxsize=1)
def _embedding_model() -> SentenceTransformer:
    try:
        return SentenceTransformer(EMBEDDING_MODEL_NAME)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load embedding model '{EMBEDDING_MODEL_NAME}': {error}",
        ) from error


def _collection_name(workspace_id: str) -> str:
    safe_workspace = re.sub(r"[^a-zA-Z0-9_-]", "_", workspace_id)
    return f"{VECTOR_COLLECTION_PREFIX}{safe_workspace}"


def _workspace_chunks_signature(chunks: list[dict]) -> str:
    digest = hashlib.sha256()
    for chunk in sorted(chunks, key=lambda item: item["chunk_id"]):
        digest.update(str(chunk["document_id"]).encode("utf-8"))
        digest.update(str(chunk["chunk_id"]).encode("utf-8"))
        digest.update(str(chunk["chunk_index"]).encode("utf-8"))
        digest.update(str(len(chunk["content"])).encode("utf-8"))
        digest.update(chunk["content"].encode("utf-8"))
    return digest.hexdigest()


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
