from app.schemas.document import DocumentChunk

DEFAULT_CHUNK_SIZE = 800
DEFAULT_OVERLAP = 100


def chunk_text(
    document_id: str,
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[DocumentChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between 0 and chunk_size - 1")

    stripped_text = text.strip()
    if not stripped_text:
        return []

    chunks: list[DocumentChunk] = []
    start_index = 0

    while start_index < len(stripped_text):
        end_index = min(start_index + chunk_size, len(stripped_text))
        content = stripped_text[start_index:end_index]
        chunk_index = len(chunks)

        chunks.append(
            DocumentChunk(
                chunk_id=f"{document_id}_chunk_{chunk_index:03d}",
                document_id=document_id,
                chunk_index=chunk_index,
                content=content,
                start_index=start_index,
                end_index=end_index,
                content_length=len(content),
            )
        )

        if end_index == len(stripped_text):
            break

        start_index = end_index - overlap

    return chunks
