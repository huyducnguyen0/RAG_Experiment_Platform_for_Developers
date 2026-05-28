# Current Phase

Current phase: Phase 6 - Simple Retrieval

Current goal:
Retrieve relevant chunks from uploaded documents using simple keyword matching.

Current constraints:
- Do not build RAG yet.
- Do not add vector database yet.
- Do not add frontend yet.
- Do not add production database yet.
- Store documents simply in local files/metadata for the MVP.

Next task:
Add keyword retrieval:
- app/api/routes/research.py
- app/schemas/research.py
- app/services/retrieval_service.py
- include research router in app/main.py

Expected behavior:
- POST /research/retrieve accepts a question and top_k.
- It returns the most relevant chunks by keyword score.
- It does not call an LLM or vector database.
