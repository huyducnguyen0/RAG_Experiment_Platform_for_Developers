# Current Phase

Current phase: Phase 5 - Document Chunking

Current goal:
Automatically split uploaded documents into small chunks for later retrieval.

Current constraints:
- Do not build RAG yet.
- Do not add vector database yet.
- Do not add frontend yet.
- Do not add production database yet.
- Store documents simply in local files/metadata for the MVP.

Next task:
Add chunking logic so uploaded documents produce reusable text chunks:
- app/services/chunking_service.py
- update app/services/document_service.py
- update app/schemas/document.py

Expected behavior:
- Uploading a document automatically creates chunks.
- Document detail includes `chunk_count`.
- Chunks are stored simply in local metadata for the MVP.
