# Current Phase

Current phase: Phase 2 - Refactor API Structure

Current goal:
Split the working `/health` and `/chat` endpoints into routes, schemas, and services without changing API behavior.

Current constraints:
- Do not build RAG yet.
- Do not add vector database yet.
- Do not add frontend yet.
- Focus only on understanding project structure, route, schema, and service.

Next task:
Refactor the Phase 1 code into:
- app/api/routes/health.py
- app/api/routes/chat.py
- app/schemas/chat.py
- app/services/chat_service.py

Expected behavior must stay the same:
- GET /health returns {"status": "ok"}
- POST /chat returns {"answer": "You asked: ..."}
