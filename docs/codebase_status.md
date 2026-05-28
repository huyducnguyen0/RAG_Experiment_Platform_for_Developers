# Codebase Status

## Current Product Shape

Agentic Research OS is currently a workspace-based RAG MVP.

The main flow is:

```text
workspace -> documents -> chunks -> keyword retrieval -> mock RAG answer -> sources
```

## Primary APIs

Workspace-scoped APIs are the main product path:

```text
POST   /workspaces
GET    /workspaces
GET    /workspaces/{workspace_id}
PATCH  /workspaces/{workspace_id}
DELETE /workspaces/{workspace_id}

POST   /workspaces/{workspace_id}/documents/upload
GET    /workspaces/{workspace_id}/documents
GET    /workspaces/{workspace_id}/documents/{document_id}
DELETE /workspaces/{workspace_id}/documents/{document_id}

POST   /workspaces/{workspace_id}/research/retrieve
POST   /workspaces/{workspace_id}/research/query
```

## Legacy APIs

These global endpoints still exist for backward compatibility and manual testing:

```text
POST   /documents/upload
GET    /documents
GET    /documents/{document_id}
DELETE /documents/{document_id}

POST   /research/retrieve
POST   /research/query
```

They are not the recommended path for the frontend because they do not scope data by workspace.

## Implemented RAG Capabilities

- Text and Markdown document upload.
- Automatic character-based chunking.
- Keyword retrieval baseline.
- Mock RAG answer generation.
- Source previews returned with answers.
- React frontend for workspace/document/query flow.

## Not Implemented Yet

- Evaluation dataset and metrics.
- Embedding/vector retrieval.
- Hybrid retrieval.
- Reranking.
- Real LLM answer mode.
- Agentic router.
- Persistent database.
- Authentication.

## Runtime Data Policy

Runtime files under `data/` are local development data and should not be committed:

```text
data/metadata.json
data/documents/*
data/workspaces/*
```

Only `.gitkeep` files should remain tracked to preserve folder structure.
