# Current Phase

Current phase: Phase 4 - Document Upload

Current goal:
Allow users to upload simple `.txt` and `.md` documents for later RAG steps.

Current constraints:
- Do not build RAG yet.
- Do not add vector database yet.
- Do not add frontend yet.
- Do not add production database yet.
- Store documents simply in local files/metadata for the MVP.

Next task:
Add document upload and listing endpoints:
- POST /documents/upload
- GET /documents
- GET /documents/{document_id}
- DELETE /documents/{document_id}

Expected behavior:
- Upload accepts only `.txt` and `.md`.
- Uploaded documents are stored locally.
- Document metadata can be listed and retrieved.
