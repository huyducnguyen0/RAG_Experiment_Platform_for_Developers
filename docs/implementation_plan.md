# Agentic Research OS - Implementation Plan

## Goal

Build a portfolio-ready MVP backend for Agentic Research OS.

Agentic Research OS is a FastAPI-based AI research assistant backend. It allows users to upload text/markdown documents, chunk them, retrieve relevant context, and generate source-grounded answers using a RAG-style pipeline.

## Current Priority

Ship a working MVP for CV/demo as fast as possible.

## Strict Rules

- Do not over-engineer.
- Do not jump phases.
- Do not implement auth/frontend/web crawling.
- Do not add unnecessary dependencies.
- Every phase must run before moving on.
- Prefer simple working code over complex architecture.
- Keep mock mode working even without external API keys.
- After each phase, explain what changed and how to test it.

## Final MVP Features

- GET /health
- POST /chat
- POST /documents/upload
- GET /documents
- GET /documents/{document_id}
- DELETE /documents/{document_id}
- POST /research/retrieve
- POST /research/query
- RAG-style answer with sources
- README demo guide

## Phase Order

### Phase 1 - Backend Skeleton

Add GET /health and POST /chat directly in app/main.py.
No refactor yet.

### Phase 2 - Refactor API Structure

Split health/chat into routes, schemas, and services.

### Phase 3 - Chat Service Mock

Move chat logic into chat_service.py and return mock answer.

### Phase 4 - Document Upload

Support .txt/.md upload and document listing.

### Phase 5 - Document Chunking

Automatically split uploaded documents into chunks.

### Phase 6 - Simple Retrieval

Implement keyword-based retrieval over chunks.

### Phase 7 - RAG Query

Implement POST /research/query using retrieval + answer generation.

### Phase 8 - Sources/Citations

Return sources with document title, chunk id, score, and excerpt.

### Phase 9 - Testing/Error Handling

Add basic tests or manual test plan. Improve common errors.

### Phase 10 - README/CV Polish

Write README, API docs, architecture docs, and demo flow.
