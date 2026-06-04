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
    top_k: int = 5,
    workspace_id: str | None = None,
    strategy: str = "keyword",
    chunks: list[dict] | None = None,
    retrieval_context_id: str | None = None,
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
            chunks=chunks,
            retrieval_context_id=retrieval_context_id,
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
            chunks=chunks,
            retrieval_context_id=retrieval_context_id,
        )

    return _retrieve_relevant_chunks_keyword(
        question=question,
        top_k=top_k,
        workspace_id=workspace_id,
        chunks=chunks,
    )


def prepare_retrieval_strategy(
    workspace_id: str,
    strategy: str,
    chunks: list[dict] | None = None,
    retrieval_context_id: str | None = None,
) -> None:
    normalized_strategy = strategy.strip().lower()
    _validate_retrieval_strategy(normalized_strategy, original_strategy=strategy)

    if normalized_strategy not in {"vector", "hybrid"}:
        return

    selected_chunks = chunks or _collect_workspace_chunks(workspace_id)
    if selected_chunks:
        _upsert_workspace_collection(
            workspace_id=workspace_id,
            chunks=selected_chunks,
            retrieval_context_id=retrieval_context_id,
        )


def _validate_retrieval_strategy(normalized_strategy: str, original_strategy: str) -> None:
    if normalized_strategy not in SUPPORTED_RETRIEVAL_STRATEGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported retrieval strategy: {original_strategy}",
        )


def _retrieve_relevant_chunks_keyword(
    question: str,
    top_k: int = 5,
    workspace_id: str | None = None,
    chunks: list[dict] | None = None,
) -> RetrieveResponse:
    keywords = _extract_keywords(question)
    results: list[RetrievedChunk] = []

    if not keywords:
        return RetrieveResponse(query=question, results=[])

    selected_chunks = chunks or _collect_workspace_chunks(workspace_id)
    for chunk in selected_chunks:
        score = _score_chunk(chunk["content"], keywords)
        if score <= 0:
            continue

        results.append(
            RetrievedChunk(
                document_id=chunk["document_id"],
                document_title=chunk["document_title"],
                chunk_id=chunk["chunk_id"],
                chunk_index=chunk["chunk_index"],
                score=float(score),
                content=chunk["content"],
                source_path=chunk.get("source_path", ""),
                relative_path=chunk.get("relative_path", ""),
                folder_path=chunk.get("folder_path", ""),
                doc_type=chunk.get("doc_type", ""),
                chunking_strategy=chunk.get("chunking_strategy", ""),
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
    chunks: list[dict] | None = None,
    retrieval_context_id: str | None = None,
) -> RetrieveResponse:
    question_text = question.strip()
    if not question_text:
        return RetrieveResponse(query=question, results=[])

    selected_chunks = chunks or _collect_workspace_chunks(workspace_id)
    if not selected_chunks:
        return RetrieveResponse(query=question, results=[])

    collection = _upsert_workspace_collection(
        workspace_id=workspace_id,
        chunks=selected_chunks,
        retrieval_context_id=retrieval_context_id,
    )
    question_embedding = _embedding_model().encode([question_text])[0].tolist()

    query_result = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(top_k, len(selected_chunks)),
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
                source_path=str(metadata.get("source_path", "")),
                relative_path=str(metadata.get("relative_path", "")),
                folder_path=str(metadata.get("folder_path", "")),
                doc_type=str(metadata.get("doc_type", "")),
                chunking_strategy=str(metadata.get("chunking_strategy", "")),
            )
        )

    return RetrieveResponse(query=question, results=results)


def _retrieve_relevant_chunks_hybrid(
    question: str,
    top_k: int,
    workspace_id: str,
    chunks: list[dict] | None = None,
    retrieval_context_id: str | None = None,
) -> RetrieveResponse:
    overfetch_k = max(top_k * 3, top_k)
    keyword_results = _retrieve_relevant_chunks_keyword(
        question=question,
        top_k=overfetch_k,
        workspace_id=workspace_id,
        chunks=chunks,
    ).results
    vector_results = _retrieve_relevant_chunks_vector(
        question=question,
        top_k=overfetch_k,
        workspace_id=workspace_id,
        chunks=chunks,
        retrieval_context_id=retrieval_context_id,
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
            source_path=by_chunk_id[chunk_id].source_path,
            relative_path=by_chunk_id[chunk_id].relative_path,
            folder_path=by_chunk_id[chunk_id].folder_path,
            doc_type=by_chunk_id[chunk_id].doc_type,
            chunking_strategy=by_chunk_id[chunk_id].chunking_strategy,
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
                    "source_path": chunk.get("source_path", document.get("source_path", "")),
                    "relative_path": chunk.get("relative_path", document.get("relative_path", "")),
                    "folder_path": chunk.get("folder_path", document.get("folder_path", "")),
                    "doc_type": chunk.get("doc_type", document.get("doc_type", "")),
                    "chunking_strategy": chunk.get("chunking_strategy", "fixed"),
                }
            )
    return chunks


def _upsert_workspace_collection(
    workspace_id: str,
    chunks: list[dict],
    retrieval_context_id: str | None = None,
):
    client = get_chroma_client()
    collection_name = _collection_name(workspace_id, retrieval_context_id)
    chunks_signature = _workspace_chunks_signature(chunks)

    if _INDEXED_WORKSPACE_SIGNATURES.get(collection_name) == chunks_signature:
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
            "source_path": chunk.get("source_path", ""),
            "relative_path": chunk.get("relative_path", ""),
            "folder_path": chunk.get("folder_path", ""),
            "doc_type": chunk.get("doc_type", ""),
            "chunking_strategy": chunk.get("chunking_strategy", ""),
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
        _INDEXED_WORKSPACE_SIGNATURES[collection_name] = chunks_signature
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


def _collection_name(workspace_id: str, retrieval_context_id: str | None = None) -> str:
    safe_workspace = re.sub(r"[^a-zA-Z0-9_-]", "_", workspace_id)
    if not retrieval_context_id:
        return f"{VECTOR_COLLECTION_PREFIX}{safe_workspace}"

    safe_context = re.sub(r"[^a-zA-Z0-9_-]", "_", retrieval_context_id)
    return f"{VECTOR_COLLECTION_PREFIX}{safe_workspace}_{safe_context}"


def _workspace_chunks_signature(chunks: list[dict]) -> str:
    digest = hashlib.sha256()
    for chunk in sorted(chunks, key=lambda item: item["chunk_id"]):
        digest.update(str(chunk["document_id"]).encode("utf-8"))
        digest.update(str(chunk["chunk_id"]).encode("utf-8"))
        digest.update(str(chunk["chunk_index"]).encode("utf-8"))
        digest.update(str(chunk.get("source_path", "")).encode("utf-8"))
        digest.update(str(chunk.get("doc_type", "")).encode("utf-8"))
        digest.update(str(chunk.get("chunking_strategy", "")).encode("utf-8"))
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
