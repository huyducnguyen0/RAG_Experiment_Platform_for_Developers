# Current Phase

Current phase: Phase 8 - Sources/Citations Polish

Current goal:
Make RAG responses clearer by polishing source/citation fields.

Current constraints:
- Do not build RAG yet.
- Do not add vector database yet.
- Do not add frontend yet.
- Do not add production database yet.
- Store documents simply in local files/metadata for the MVP.

Next task:
Improve source output:
- Add source_id mapping.
- Keep document_title, chunk_id, score, and excerpt/preview clear.
- Optionally mention source numbers in the mock answer.

Expected behavior:
- POST /research/query returns answer + readable sources.
- Each source is easy to map back to a document chunk.
- Still no frontend, auth, vector DB, or real LLM required.
