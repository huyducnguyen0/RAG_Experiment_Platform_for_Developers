from app.schemas.document import DocumentChunk
from app.schemas.rag_config import RagConfigPreset
from langchain_text_splitters import RecursiveCharacterTextSplitter

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
                original_text=content,
                headline=_infer_chunk_headline(content),
                start_index=start_index,
                end_index=end_index,
                content_length=len(content),
            )
        )

        if end_index == len(stripped_text):
            break

        start_index = end_index - overlap

    return chunks


def chunk_text_for_rag_config(
    document_id: str,
    text: str,
    rag_config: RagConfigPreset,
) -> list[DocumentChunk]:
    chunking_type = rag_config.chunking.type.strip().lower()
    params = rag_config.chunking.params

    if chunking_type == "paragraph":
        return chunk_text_by_paragraphs(
            document_id=document_id,
            text=text,
            max_chunk_size=int(params.get("max_chunk_size", DEFAULT_CHUNK_SIZE)),
        )
    if chunking_type == "recursive_character":
        return chunk_text_recursive_character(
            document_id=document_id,
            text=text,
            chunk_size=int(params.get("chunk_size", DEFAULT_CHUNK_SIZE)),
            overlap=int(params.get("overlap", DEFAULT_OVERLAP)),
        )

    return chunk_text(
        document_id=document_id,
        text=text,
        chunk_size=int(params.get("chunk_size", DEFAULT_CHUNK_SIZE)),
        overlap=int(params.get("overlap", DEFAULT_OVERLAP)),
    )


def chunk_text_by_paragraphs(
    document_id: str,
    text: str,
    max_chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> list[DocumentChunk]:
    if max_chunk_size <= 0:
        raise ValueError("max_chunk_size must be greater than 0")

    stripped_text = text.strip()
    if not stripped_text:
        return []

    paragraphs = [item.strip() for item in stripped_text.splitlines() if item.strip()]
    if not paragraphs:
        return []

    chunks: list[DocumentChunk] = []
    current_parts: list[str] = []
    current_start = 0
    search_from = 0

    for paragraph in paragraphs:
        paragraph_start = stripped_text.find(paragraph, search_from)
        if paragraph_start == -1:
            paragraph_start = search_from
        paragraph_end = paragraph_start + len(paragraph)
        candidate = "\n\n".join([*current_parts, paragraph]) if current_parts else paragraph

        if current_parts and len(candidate) > max_chunk_size:
            content = "\n\n".join(current_parts)
            chunks.append(_build_chunk(document_id, chunks, content, current_start))
            current_parts = [paragraph]
            current_start = paragraph_start
        else:
            if not current_parts:
                current_start = paragraph_start
            current_parts.append(paragraph)

        search_from = paragraph_end

    if current_parts:
        content = "\n\n".join(current_parts)
        chunks.append(_build_chunk(document_id, chunks, content, current_start))

    return chunks


def chunk_text_recursive_character(
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

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
    )
    split_texts = splitter.split_text(stripped_text)
    chunks: list[DocumentChunk] = []
    search_from = 0

    for content in split_texts:
        start_index = stripped_text.find(content, max(search_from - overlap, 0))
        if start_index == -1:
            start_index = search_from
        chunks.append(_build_chunk(document_id, chunks, content, start_index))
        search_from = start_index + len(content)

    return chunks


def _build_chunk(
    document_id: str,
    chunks: list[DocumentChunk],
    content: str,
    start_index: int,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=f"{document_id}_chunk_{len(chunks):03d}",
        document_id=document_id,
        chunk_index=len(chunks),
        content=content,
        original_text=content,
        headline=_infer_chunk_headline(content),
        start_index=start_index,
        end_index=start_index + len(content),
        content_length=len(content),
    )


def _infer_chunk_headline(content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip().strip("#").strip()
        if stripped:
            return stripped[:120]
    return ""
