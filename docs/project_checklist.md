# Project Checklist: Agentic Research OS

> Purpose: This checklist is the single source of truth for building the project step by step.  
> Use this file with Codex/AI coding agents so they understand the current phase, the next task, and the expected output.

---

## Core Principle

Follow this loop for every feature:

```text
Make it work -> Make it clean -> Make it better
```

Meaning:

1. First, make the feature run in the simplest possible way.
2. Test it manually.
3. Only after it works, refactor into cleaner files such as service/schema/config.
4. Test again after refactor.
5. Do not optimize too early.

---

## Global Rules for Codex / AI Agent

- Read this checklist before coding.
- Do not jump ahead to future phases.
- Do not add technologies that are not needed for the current phase.
- Keep each change small and testable.
- Explain every step in Vietnamese.
- Before editing code, state:
  - current phase
  - current task
  - files to be changed
  - expected result
- After editing code, state:
  - what changed
  - how to run
  - how to test
  - expected output
  - common errors
- Do not delete files unless explicitly asked.
- Do not expose API keys.
- Do not modify `.env` directly except when creating `.env.example`.
- Prefer `uv` commands.

---

## Target Project Structure

The project should gradually evolve toward:

```text
agentic-research-os/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   └── document.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_service.py
│   │   ├── llm_service.py
│   │   ├── document_service.py
│   │   ├── chunk_service.py
│   │   ├── embedding_service.py
│   │   ├── vector_store_service.py
│   │   ├── rag_service.py
│   │   └── agent_service.py
│   └── utils/
│       └── __init__.py
├── scripts/
├── tests/
├── docs/
│   ├── project_checklist.md
│   └── current_phase.md
├── data/
├── .env.example
├── pyproject.toml
├── uv.lock
└── README.md
```

Do not create all files at once if they are not needed yet. Add them gradually.

---

# Phase 0: Project Foundation

## Goal

Understand how the project runs and prepare the minimal development environment.

## Concepts to Understand

- `uv`
- virtual environment
- `pyproject.toml`
- `uv.lock`
- FastAPI entry point
- `app.main:app`
- project root
- import path
- `.env`
- config
- script
- Git workflow

## Checklist

- [ ] Confirm project runs inside the correct virtual environment.
- [ ] Confirm `uv` is installed and usable.
- [ ] Confirm `pyproject.toml` exists.
- [ ] Confirm `uv.lock` exists after dependencies are installed.
- [ ] Install FastAPI if needed.
- [ ] Create minimal `app/main.py` if it does not exist.
- [ ] Run FastAPI server successfully.
- [ ] Open Swagger UI successfully.
- [ ] Understand what `uv run uvicorn app.main:app --reload` means.
- [ ] Create `docs/current_phase.md`.
- [ ] Create or verify `AGENTS.md` for Codex instructions.

## Useful Commands

```bash
uv add "fastapi[standard]"
uv run uvicorn app.main:app --reload
```

## Definition of Done

- [ ] Server runs at `http://127.0.0.1:8000`.
- [ ] Swagger UI opens at `http://127.0.0.1:8000/docs`.
- [ ] User can explain what `app.main:app` means.
- [ ] Codex can read `docs/project_checklist.md` and `docs/current_phase.md`.

## Expected Output

```text
Uvicorn running on http://127.0.0.1:8000
```

---

# Phase 1: Backend Skeleton

## Goal

Build a clean minimal FastAPI backend with `/health` and `/chat`.

## Principle for This Phase

Start simple. It is acceptable to first put code in `main.py`. Once it works, refactor into:

- `app/api/routes.py`
- `app/schemas/chat.py`
- `app/services/chat_service.py`
- `app/core/config.py` if needed

## Concepts to Understand

- API
- endpoint
- route
- request
- response
- JSON
- HTTP method
- Pydantic schema
- service layer
- refactor

## Checklist

### 1. Minimal Working Version

- [ ] Create `app/main.py`.
- [ ] Create FastAPI app object.
- [ ] Create `GET /health`.
- [ ] Create basic `POST /chat`.
- [ ] Define `ChatRequest` with `question: str`.
- [ ] Return fake answer from `/chat`.
- [ ] Run server.
- [ ] Test `/health`.
- [ ] Test `/chat` in Swagger UI.

### 2. Refactor After It Runs

- [ ] Create `app/api/`.
- [ ] Create `app/schemas/`.
- [ ] Create `app/services/`.
- [ ] Move endpoint definitions to `app/api/routes.py`.
- [ ] Move request/response models to `app/schemas/chat.py`.
- [ ] Move chat logic to `app/services/chat_service.py`.
- [ ] Keep `app/main.py` responsible only for creating app and including router.
- [ ] Test `/health` again.
- [ ] Test `/chat` again.

## Useful Commands

```bash
uv run uvicorn app.main:app --reload
```

## Expected API

### `GET /health`

Expected response:

```json
{
  "status": "ok"
}
```

### `POST /chat`

Request:

```json
{
  "question": "RAG là gì?"
}
```

Expected response:

```json
{
  "answer": "You asked: RAG là gì?"
}
```

## Definition of Done

- [ ] `/health` works.
- [ ] `/chat` works.
- [ ] Swagger UI shows both endpoints.
- [ ] Code is separated into route/schema/service after initial working version.
- [ ] User can explain the request flow:

```text
User -> /chat endpoint -> ChatRequest -> chat_service -> ChatResponse -> JSON response
```

---

# Phase 2: Config and Environment Variables

## Goal

Move environment-specific values out of code and into `.env` / config.

## Concepts to Understand

- `.env`
- `.env.example`
- environment variable
- config object
- secret management
- app settings

## Checklist

- [ ] Create `.env.example`.
- [ ] Add placeholder variables such as `APP_NAME`, `MODEL_NAME`, `OPENAI_API_KEY`.
- [ ] Add `.env` to `.gitignore` if not already ignored.
- [ ] Create `app/core/config.py`.
- [ ] Load config using Pydantic settings or simple environment loading.
- [ ] Use config in `main.py` or service where appropriate.
- [ ] Confirm app still runs.
- [ ] Confirm no secret is committed.

## Example `.env.example`

```env
APP_NAME=Agentic Research OS
MODEL_NAME=gpt-4.1-mini
OPENAI_API_KEY=your_api_key_here
```

## Useful Commands

```bash
uv add pydantic-settings python-dotenv
uv run uvicorn app.main:app --reload
```

## Definition of Done

- [ ] Config values are not hardcoded unnecessarily.
- [ ] `.env.example` exists.
- [ ] `.env` is ignored by Git.
- [ ] App can read config.
- [ ] App still runs after config refactor.

---

# Phase 3: Real LLM Call

## Goal

Make `/chat` call a real LLM provider instead of returning a fake answer.

## Principle for This Phase

First make a simple direct LLM call work. Then refactor into `llm_service.py`.

## Concepts to Understand

- LLM provider
- API key
- model name
- request/response from LLM
- error handling
- timeout
- cost awareness

## Checklist

### 1. Make It Work

- [ ] Add required LLM SDK or client.
- [ ] Add `OPENAI_API_KEY` or equivalent to `.env`.
- [ ] Write a simple function to send prompt to model.
- [ ] Connect `/chat` to the LLM function.
- [ ] Test with a simple question.

### 2. Make It Clean

- [ ] Create `app/services/llm_service.py`.
- [ ] Move LLM calling logic into `llm_service.py`.
- [ ] Keep `chat_service.py` responsible for chat-level flow.
- [ ] Add basic error handling.
- [ ] Test `/chat` again.

## Useful Commands

```bash
uv add openai
uv run uvicorn app.main:app --reload
```

## Definition of Done

- [ ] `/chat` returns a real model answer.
- [ ] API key is read from environment, not hardcoded.
- [ ] LLM logic is inside `llm_service.py`.
- [ ] User understands the difference between `chat_service` and `llm_service`.

---

# Phase 4: Document Loading

## Goal

Load documents from files and extract raw text.

## Principle for This Phase

Start with `.txt` or `.md`. Add PDF later.

## Concepts to Understand

- document loader
- raw text
- file path
- file storage
- metadata
- script vs API endpoint

## Checklist

### 1. Script First

- [ ] Create `scripts/test_load_document.py`.
- [ ] Create sample file in `data/sample.txt`.
- [ ] Load text from the file.
- [ ] Print first 500 characters.
- [ ] Print metadata such as filename and length.

### 2. Refactor Into Service

- [ ] Create `app/services/document_service.py`.
- [ ] Move loading logic into service.
- [ ] Return structured document object or dictionary.
- [ ] Test service with script.

### 3. Optional API

- [ ] Add `POST /documents/load` or similar only if needed.
- [ ] Return loaded document metadata.

## Useful Commands

```bash
uv run python scripts/test_load_document.py
```

## Definition of Done

- [ ] A text/markdown file can be loaded.
- [ ] The script prints document content preview.
- [ ] Document metadata is available.
- [ ] Logic is moved to `document_service.py` after it works.

---

# Phase 5: Text Chunking

## Goal

Split raw document text into smaller chunks suitable for retrieval.

## Concepts to Understand

- chunk
- chunk size
- overlap
- metadata per chunk
- token vs character length

## Checklist

### 1. Make Simple Chunker

- [ ] Create `scripts/test_chunk_text.py`.
- [ ] Load sample document.
- [ ] Split text by characters or paragraphs.
- [ ] Print number of chunks.
- [ ] Print first few chunks.

### 2. Add Metadata

- [ ] Add `chunk_id`.
- [ ] Add `source`.
- [ ] Add `start_index` / `end_index` if useful.
- [ ] Add approximate length.

### 3. Refactor

- [ ] Create `app/services/chunk_service.py`.
- [ ] Move chunking logic into service.
- [ ] Test again through script.

## Useful Commands

```bash
uv run python scripts/test_chunk_text.py
```

## Definition of Done

- [ ] Raw text can be split into chunks.
- [ ] Each chunk has text and metadata.
- [ ] Chunking logic is reusable from service.
- [ ] User understands why chunking is needed for RAG.

---

# Phase 6: Simple Keyword Search Before Vector DB

## Goal

Build a simple retrieval system before using embeddings/vector DB.

## Reason

This helps the user understand retrieval before adding vector complexity.

## Concepts to Understand

- retrieval
- query
- ranking
- keyword search
- relevance
- top-k

## Checklist

- [ ] Create sample chunks.
- [ ] Write simple keyword matching function.
- [ ] Rank chunks by number of keyword matches.
- [ ] Return top-k chunks.
- [ ] Create `scripts/test_keyword_search.py`.
- [ ] Test with multiple queries.
- [ ] Refactor to retrieval service if needed.

## Useful Commands

```bash
uv run python scripts/test_keyword_search.py
```

## Definition of Done

- [ ] User can ask a query.
- [ ] System returns most relevant chunks using simple search.
- [ ] User understands retrieval without embeddings.

---

# Phase 7: Embedding Service

## Goal

Convert text chunks and queries into embedding vectors.

## Concepts to Understand

- embedding
- vector
- embedding model
- query embedding
- document embedding
- batch embedding
- cost

## Checklist

### 1. Make It Work in Script

- [ ] Create `scripts/test_embedding.py`.
- [ ] Embed one sentence.
- [ ] Print vector length.
- [ ] Embed multiple chunks.
- [ ] Confirm output shape.

### 2. Refactor

- [ ] Create `app/services/embedding_service.py`.
- [ ] Move embedding logic into service.
- [ ] Support batch input.
- [ ] Add basic error handling.

## Useful Commands

```bash
uv run python scripts/test_embedding.py
```

## Definition of Done

- [ ] Text can be converted into vectors.
- [ ] Embedding service can embed a list of chunks.
- [ ] User understands why vectors are needed for semantic search.

---

# Phase 8: Vector Database

## Goal

Store chunks and embeddings in a vector database and search by similarity.

## Recommended First Choice

Use ChromaDB first because it is simple for local development.

## Concepts to Understand

- vector database
- collection
- add documents
- query
- cosine similarity
- top-k
- persistence

## Checklist

### 1. Make It Work in Script

- [ ] Install ChromaDB.
- [ ] Create `scripts/test_vector_store.py`.
- [ ] Create collection.
- [ ] Add sample chunks and embeddings.
- [ ] Query with a question.
- [ ] Print top-k results.

### 2. Refactor

- [ ] Create `app/services/vector_store_service.py`.
- [ ] Move add/search logic into service.
- [ ] Support metadata.
- [ ] Support persistent DB path.
- [ ] Test again.

## Useful Commands

```bash
uv add chromadb
uv run python scripts/test_vector_store.py
```

## Definition of Done

- [ ] Chunks are stored in vector DB.
- [ ] Query returns relevant chunks.
- [ ] Metadata is preserved.
- [ ] Vector store logic is reusable from service.

---

# Phase 9: Basic RAG

## Goal

Connect retrieval with LLM generation.

## Flow

```text
User question
  -> embed query
  -> search vector DB
  -> get top-k chunks
  -> build prompt with context
  -> call LLM
  -> return answer + sources
```

## Concepts to Understand

- RAG
- context injection
- prompt template
- source citation
- hallucination
- grounded answer
- token limit

## Checklist

### 1. Make Basic RAG Work

- [ ] Create `app/services/rag_service.py`.
- [ ] Implement retrieve step.
- [ ] Implement prompt-building step.
- [ ] Call LLM with context.
- [ ] Return answer.
- [ ] Return sources.
- [ ] Connect `/chat` to RAG when documents exist.

### 2. Test

- [ ] Add a sample document.
- [ ] Index the document.
- [ ] Ask a question about the document.
- [ ] Confirm answer uses document context.
- [ ] Confirm sources are returned.

## Expected Response Shape

```json
{
  "answer": "...",
  "sources": [
    {
      "source": "sample.txt",
      "chunk_id": "sample_001"
    }
  ]
}
```

## Definition of Done

- [ ] `/chat` can answer using uploaded/indexed document context.
- [ ] Answer includes sources.
- [ ] User can explain the RAG flow.
- [ ] RAG logic is separated from route layer.

---

# Phase 10: Chat History and Memory

## Goal

Allow the chatbot to remember previous messages in a conversation.

## Concepts to Understand

- session
- conversation
- message
- role: user / assistant / system
- short-term memory
- database persistence

## Checklist

### 1. In-Memory First

- [ ] Create simple in-memory conversation store.
- [ ] Store user messages.
- [ ] Store assistant messages.
- [ ] Send recent history to LLM.
- [ ] Test multi-turn conversation.

### 2. Persistent Storage Later

- [ ] Add SQLite or Postgres when needed.
- [ ] Create conversations table.
- [ ] Create messages table.
- [ ] Save messages after each chat.
- [ ] Retrieve recent messages by conversation ID.

## Definition of Done

- [ ] User can continue a conversation across multiple messages.
- [ ] The system uses recent history in response generation.
- [ ] User understands the difference between RAG context and chat history.

---

# Phase 11: Agentic Router

## Goal

Do not use RAG for every question. Add a router that decides whether to use documents, answer directly, rewrite query, or ask for clarification.

## Concepts to Understand

- agent
- router
- tool calling
- decision step
- query rewriting
- direct answer vs RAG answer
- agent state

## Checklist

### 1. Simple Rule-Based Router

- [ ] Create `app/services/agent_service.py`.
- [ ] Add simple rule: if question mentions uploaded docs/current document/source, use RAG.
- [ ] Otherwise answer directly.
- [ ] Test both paths.

### 2. LLM-Based Router Later

- [ ] Ask LLM to classify user intent.
- [ ] Possible routes:
  - direct_answer
  - rag_answer
  - summarize_document
  - compare_sources
  - ask_clarification
- [ ] Add structured output for routing decision.
- [ ] Log routing decision for debugging.

## Definition of Done

- [ ] The system does not always use RAG.
- [ ] Direct questions can be answered directly.
- [ ] Document-specific questions use RAG.
- [ ] Router decision is visible in logs or debug output.

---

# Phase 12: RAG Evaluation

## Goal

Evaluate whether retrieval and answers are actually good.

## Concepts to Understand

- golden dataset
- retrieval metrics
- precision
- recall
- MRR
- NDCG
- faithfulness
- answer relevance
- LLM-as-judge
- latency
- cost

## Checklist

### 1. Golden Dataset

- [ ] Create `eval/golden_questions.jsonl` or similar.
- [ ] Add question.
- [ ] Add expected answer.
- [ ] Add expected relevant chunks.

### 2. Retrieval Evaluation

- [ ] Measure whether expected chunks appear in top-k.
- [ ] Compute simple recall@k.
- [ ] Compute precision@k if useful.

### 3. Answer Evaluation

- [ ] Use simple manual review first.
- [ ] Add LLM-as-judge later.
- [ ] Score faithfulness.
- [ ] Score relevance.

### 4. Report

- [ ] Print evaluation summary.
- [ ] Save eval results.
- [ ] Compare changes across experiments.

## Definition of Done

- [ ] There is a small test set.
- [ ] Retrieval can be measured.
- [ ] Answer quality can be reviewed.
- [ ] User can improve RAG scientifically instead of guessing.

---

# Phase 13: UI

## Goal

Build a simple user interface for chat, document upload, and source display.

## Options

Start simple:

- Gradio
- Streamlit

More portfolio-ready:

- React
- Next.js
- Tailwind CSS

## Checklist

### 1. Minimal UI

- [ ] Create chat input.
- [ ] Display assistant answer.
- [ ] Display sources.
- [ ] Add document upload if backend supports it.

### 2. Better UI

- [ ] Add conversation sidebar.
- [ ] Add document list.
- [ ] Add retrieved context viewer.
- [ ] Add loading state.
- [ ] Add error display.

## Definition of Done

- [ ] User can chat through UI.
- [ ] User can see sources.
- [ ] User can upload or select documents if supported.
- [ ] UI is usable enough for demo.

---

# Phase 14: Authentication and Workspace

## Goal

Support multiple users and private documents.

## Concepts to Understand

- user
- authentication
- authorization
- JWT
- password hashing
- workspace
- multi-tenant data

## Checklist

- [ ] Add users table.
- [ ] Add register/login endpoints.
- [ ] Hash passwords.
- [ ] Issue JWT access token.
- [ ] Protect private endpoints.
- [ ] Associate documents with user ID.
- [ ] Associate conversations with user ID.
- [ ] Test user A cannot access user B documents.

## Definition of Done

- [ ] Users can log in.
- [ ] User data is separated.
- [ ] Private documents are protected.

---

# Phase 15: Deployment

## Goal

Deploy the project so it can be used from the internet.

## Concepts to Understand

- Docker
- Docker Compose
- production config
- environment variables
- server logs
- database migration
- cloud deployment
- monitoring

## Checklist

### 1. Prepare for Deployment

- [ ] Create `.env.example`.
- [ ] Create production-safe config.
- [ ] Add README instructions.
- [ ] Add health check.
- [ ] Make sure app runs from clean setup.

### 2. Docker

- [ ] Create `Dockerfile`.
- [ ] Create `.dockerignore`.
- [ ] Build Docker image locally.
- [ ] Run container locally.

### 3. Deploy

- [ ] Choose backend host: Render / Railway / Fly.io / VPS.
- [ ] Choose frontend host: Vercel / Netlify if needed.
- [ ] Choose DB provider: Supabase / Neon / Railway Postgres.
- [ ] Configure environment variables.
- [ ] Deploy.
- [ ] Test production URL.

## Definition of Done

- [ ] App is accessible from public URL.
- [ ] `/health` works in production.
- [ ] README explains setup and deployment.
- [ ] Secrets are not committed.

---

# Phase 16: Portfolio Polish

## Goal

Make the project presentable for GitHub, internship, interview, or demo.

## Checklist

- [ ] Write clear README.
- [ ] Add project motivation.
- [ ] Add architecture diagram.
- [ ] Add setup instructions.
- [ ] Add API examples.
- [ ] Add screenshots.
- [ ] Add demo video or GIF.
- [ ] Add limitations section.
- [ ] Add future improvements section.
- [ ] Add evaluation results.
- [ ] Clean unused files.
- [ ] Ensure project can run from fresh clone.

## Definition of Done

- [ ] A stranger can understand what the project does from README.
- [ ] A stranger can run the project locally.
- [ ] Project shows backend, AI, RAG, eval, and deployment thinking.

---

# Current Recommended Execution Order

Use this as the practical order:

```text
1. Phase 0: Project Foundation
2. Phase 1: Backend Skeleton
3. Phase 2: Config and Environment Variables
4. Phase 3: Real LLM Call
5. Phase 4: Document Loading
6. Phase 5: Text Chunking
7. Phase 6: Simple Keyword Search
8. Phase 7: Embedding Service
9. Phase 8: Vector Database
10. Phase 9: Basic RAG
11. Phase 10: Chat History
12. Phase 11: Agentic Router
13. Phase 12: RAG Evaluation
14. Phase 13: UI
15. Phase 15: Deployment
16. Phase 16: Portfolio Polish
```

Authentication/workspace can be delayed unless the project needs multiple users.

---

# Daily Workflow

At the start of each work session:

- [ ] Open project root in IDE.
- [ ] Ask Codex to read `AGENTS.md`, `docs/project_checklist.md`, and `docs/current_phase.md`.
- [ ] Ask Codex to identify current phase and next smallest task.
- [ ] Do one checklist item only.
- [ ] Run/test manually.
- [ ] If success, update checklist.
- [ ] Commit small change.

## Suggested Git Commit Style

```bash
git add .
git commit -m "Add basic FastAPI health endpoint"
```

---

# Standard Prompt for Codex

Use this prompt when starting a new Codex session:

```text
Đọc `AGENTS.md`, `docs/project_checklist.md`, `docs/current_phase.md` và cấu trúc project hiện tại.

Sau đó trả lời bằng tiếng Việt:

1. Project hiện tại đang ở phase nào?
2. Mục tiêu gần nhất là gì?
3. Những file nào hiện đã có?
4. Những file nào còn thiếu?
5. Bước nhỏ tiếp theo nên làm là gì?

Chưa sửa code ở prompt này.
```

---

# Standard Prompt for One Small Task

```text
Làm đúng một bước nhỏ tiếp theo trong `docs/current_phase.md`.

Yêu cầu:
- Không nhảy phase.
- Không thêm RAG/database/vector DB/frontend nếu chưa đến phase đó.
- Trước khi sửa, nói rõ sẽ sửa file nào.
- Sau khi sửa, giải thích từng file dùng để làm gì.
- Đưa lệnh chạy bằng `uv`.
- Đưa cách test trong browser hoặc Swagger UI.
- Nếu có lỗi thường gặp, giải thích cách sửa.
```

---

# Standard Prompt for Debugging

```text
Tao gặp lỗi này khi chạy project:

```bash
PASTE_ERROR_HERE
```

Hãy debug theo quy trình:

1. Đọc lỗi từ trên xuống dưới.
2. Chỉ ra dòng lỗi quan trọng nhất.
3. Giải thích lỗi bằng tiếng Việt dễ hiểu.
4. Chỉ ra nguyên nhân khả dĩ nhất trong project này.
5. Đề xuất cách sửa nhỏ nhất.
6. Nếu cần sửa code, chỉ sửa đúng phần gây lỗi.
7. Sau khi sửa, đưa lệnh chạy lại.
```

---

# Standard Prompt for Refactor

```text
Code hiện tại đã chạy được. Bây giờ refactor cho sạch theo nguyên tắc:

Make it work -> Make it clean -> Make it better

Yêu cầu:
- Không đổi behavior của API.
- Chỉ tách code ra các file hợp lý.
- Sau refactor, API cũ vẫn phải chạy y hệt.
- Giải thích trước/sau refactor khác nhau như nào.
- Đưa lệnh test lại.
```

---

# Notes for the User

If you feel lost, do not ask Codex to build the whole project. Ask it:

```text
Bước nhỏ tiếp theo là gì? Chỉ hướng dẫn tao làm một bước thôi.
```

The goal is not to finish fast. The goal is to build the project while understanding every layer.
