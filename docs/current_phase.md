# Current Phase

Current phase: Phase 7 - RAG Query

Current goal:
Answer research questions using retrieved document chunks as context.

Current constraints:
- Do not build RAG yet.
- Do not add vector database yet.
- Do not add frontend yet.
- Do not add production database yet.
- Store documents simply in local files/metadata for the MVP.

Next task:
Add RAG-style query flow:
- POST /research/query
- app/services/ai_service.py
- app/services/rag_service.py
- update app/schemas/research.py
- update app/api/routes/research.py

Expected behavior:
- POST /research/query retrieves chunks, builds context, and returns answer + sources.
- It works in mock mode without API keys.
- If no chunks match, it says the documents do not contain enough information.
