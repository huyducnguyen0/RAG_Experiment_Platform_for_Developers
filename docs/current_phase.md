# Current Phase

Current phase: Phase 3 - Chat Service Mock

Current goal:
Make the chat service more structured so it can later be replaced by real LLM/RAG logic.

Current constraints:
- Do not build RAG yet.
- Do not add vector database yet.
- Do not add frontend yet.
- Focus only on understanding project structure, route, schema, and service.

Next task:
Update the chat flow so:
- app/api/routes/chat.py stays thin.
- app/services/chat_service.py owns the mock answer logic.
- app/schemas/chat.py returns a structured response with `answer` and `mode`.

Expected behavior must stay the same:
- GET /health returns {"status": "ok"}
- POST /chat returns a mock answer and mode metadata.
