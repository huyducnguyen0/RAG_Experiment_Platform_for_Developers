# Next Session Instructions

Use this file at the start of the next chat. It is written for a new AI assistant that has not seen the previous conversation.

## Prompt To Give The New AI

```text
Đọc kỹ các file sau trước khi trả lời hoặc sửa code:

- AGENTS.md
- docs/project_checklist.md
- docs/current_phase.md
- docs/next_session_instructions.md
- docs/next_chat_handoff.md
- docs/codebase_status.md
- docs/feature_status.md
- docs/evaluation.md
- docs/rag_experiment_product_plan.md

Sau khi đọc xong, trả lời bằng tiếng Việt:

1. Project hiện tại đang ở phase nào?
2. Những phần nào đã hoàn thành?
3. Bước tiếp theo nên làm là gì?
4. Kế hoạch implement chi tiết là gì?
5. Sẽ sửa những file nào?

Chưa sửa code cho đến khi trình bày kế hoạch xong.
```

## Project Identity

Project name:

```text
RAG Experiment Platform for Developers
```

The product is a developer-focused RAG experiment platform. The user uploads a corpus and golden questions, then the platform evaluates many RAG configurations through multiple phases.

The product is not just a chatbot. The core value is:

```text
scientific RAG evaluation -> leaderboard -> candidate pool -> phase artifacts -> controlled next-phase experiments
```

## Current Phase

Current phase:

```text
Phase 12 / Eval 7 - Multi-Phase RAG Experiment Pipeline
```

The current active evaluation phases are:

```text
chunking_evaluation
retriever_evaluation
```

Future phases are still planned/disabled:

```text
query_transform_evaluation
reranker_evaluation
context_builder_evaluation
answer_evaluation
```

## Important Product Rule

Do not pick final top 5 too early.

Correct strategy:

```text
evaluate one RAG phase
-> keep candidate pool
-> use the candidate pool as input for the next phase
-> prune gradually
-> export final top 5 only at the end
```

Current chunking rule:

```text
7 chunking configs -> keep top 3 -> use those top 3 for retriever evaluation later
```

## What Was Completed Recently

### 1. Folder / Corpus Upload

The frontend Documents tab now supports selecting a nested folder.

Backend endpoint:

```text
POST /workspaces/{workspace_id}/documents/upload-folder
```

Behavior:

- Accepts many uploaded files.
- Imports only `.txt` and `.md`.
- Skips unsupported files.
- Preserves browser relative path through `relative_paths_json`.

Example metadata:

```json
{
  "source_path": "policy/refund.md",
  "relative_path": "policy/refund.md",
  "folder_path": "policy",
  "doc_type": "policy",
  "file_extension": ".md"
}
```

The `doc_type` rule follows the training example the user pasted:

```text
doc_type = first folder under corpus root
```

Examples:

```text
policy/refund.md -> doc_type = policy
claims/nested/claim.txt -> doc_type = claims
file_at_root.md -> doc_type = root
```

### 2. Rich Document And Chunk Metadata

Document schema now includes:

```text
source_path
relative_path
folder_path
doc_type
file_extension
```

Chunk schema now includes:

```text
original_text
headline
summary
source_path
relative_path
folder_path
doc_type
file_extension
chunking_strategy
chunk_size
chunk_overlap
```

Important:

- `headline` is currently inferred from the first non-empty line.
- `summary` is currently empty.
- LLM chunking with generated headline/summary is planned later, not active yet.

### 3. Runnable Chunking Evaluation

`chunking_evaluation` is now a real runnable phase.

Current 7 chunking configs:

```text
cfg_chunk_fixed_500_50
cfg_chunk_fixed_800_100
cfg_chunk_fixed_1200_150
cfg_chunk_paragraph_1000
cfg_chunk_recursive_500_200
cfg_chunk_recursive_800_200
cfg_chunk_recursive_1000_250
```

Chunking families:

```text
fixed character
paragraph
recursive character
```

Recursive character splitting uses:

```text
langchain-text-splitters
RecursiveCharacterTextSplitter
```

The project added dependency:

```text
langchain-text-splitters
```

### 4. Chunking Metrics

The experiment metrics now include:

```text
hit_at_k
recall_at_k
precision_at_k
mrr
avg_latency_ms
chunk_count
avg_chunk_size
min_chunk_size
max_chunk_size
coverage_ratio
```

For chunking evaluation, golden question `expected_chunk_ids` are treated as evidence anchors:

```text
expected_chunk_ids -> original uploaded chunk content -> evidence text
runtime chunks -> content-overlap scoring against evidence text
```

This is necessary because different chunking strategies produce different chunk ids and boundaries.

### 5. Phase Artifacts

Every compare run creates a persisted artifact:

```text
data/workspaces/{workspace_id}/phase_artifacts/artifact_*.json
```

Artifact API:

```text
GET /workspaces/{workspace_id}/phase-artifacts
GET /workspaces/{workspace_id}/phase-artifacts/latest?phase_id=chunking_evaluation
GET /workspaces/{workspace_id}/phase-artifacts/{artifact_id}
```

The latest artifact card appears in the frontend after compare.

## Current Working Flow

```text
1. Start backend
2. Start frontend
3. Create/select workspace
4. Upload nested corpus folder or individual .txt/.md files
5. Upload golden_questions.jsonl
6. Select Chunking Evaluation
7. Compare rag_config presets
8. Inspect leaderboard
9. Inspect latest phase artifact
10. Keep top 3 chunking configs for the next phase
```

## Commands

Backend:

```powershell
cd D:\AI\projects\RAG_Experiment_Platform_for_Developers
uv run uvicorn app.main:app --reload
```

Frontend:

```powershell
cd D:\AI\projects\RAG_Experiment_Platform_for_Developers\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Checks:

```powershell
uv run python -m compileall app
cd frontend
npm run build
```

## Last Verified Smoke Tests

Folder upload was tested:

```text
folder upload 200
folder result 2 imported, 1 skipped
policy/refund.md -> doc_type policy
claims/nested/claim.txt -> doc_type claims
```

Chunking compare was tested:

```text
chunk compare 200
chunk configs 7
kept/total 3/7
```

Example top rows:

```text
cfg_chunk_paragraph_1000      kept
cfg_chunk_fixed_1200_150      kept
cfg_chunk_recursive_1000_250  kept
cfg_chunk_fixed_800_100       pruned
```

## Most Important Current Files

Backend:

```text
app/api/routes/workspaces.py
app/schemas/document.py
app/schemas/experiment.py
app/schemas/phase_artifact.py
app/schemas/rag_config.py
app/schemas/rag_phase.py
app/schemas/research.py
app/services/document_service.py
app/services/chunking_service.py
app/services/retrieval_service.py
app/services/evaluation_service.py
app/services/experiment_service.py
app/services/phase_artifact_service.py
app/services/rag_config_service.py
app/services/rag_phase_service.py
```

Frontend:

```text
frontend/src/App.tsx
frontend/src/api/client.ts
frontend/src/types/api.ts
frontend/src/index.css
```

Docs:

```text
docs/project_checklist.md
docs/current_phase.md
docs/next_chat_handoff.md
docs/codebase_status.md
docs/feature_status.md
docs/evaluation.md
docs/rag_experiment_product_plan.md
docs/system_map.md
```

## Next Recommended Feature

Build:

```text
Query Transform Evaluation Foundation
```

Current retriever phase now consumes the strongest chunking candidates from the latest `chunking_evaluation` artifact. The next feature should make query transform evaluation consume the strongest retriever candidates from the latest `retriever_evaluation` artifact.

## Goal Of Next Feature

Use the top retriever candidates as input to query transform evaluation.

Expected flow:

```text
latest retriever_evaluation artifact
-> read kept_config_ids
-> keep each selected retriever candidate's chunking + retriever setup
-> add query transform candidates
-> run retrieval benchmark
-> save query_transform_evaluation artifact
```

Example:

```text
Top 5 retriever configs:
- cfg_retriever__chunk_paragraph_1000__keyword
- cfg_retriever__chunk_paragraph_1000__vector
- cfg_retriever__chunk_fixed_1200_150__hybrid

Query transform candidates:
- none
- simple rewrite

Total query transform candidates:
5 retriever configs x 2 query transforms = 10 configs
```

Candidate pool rule for this next phase:

```text
10 query transform candidates -> keep top 5
```

## Suggested Implementation Plan For Next AI

### Step 1 - Read Latest Retriever Artifact

Use:

```text
get_latest_phase_artifact(workspace_id, phase_id="retriever_evaluation")
```

If missing, return a clear 400 message:

```text
Run retriever evaluation before query transform evaluation.
```

### Step 2 - Model Query Transform Candidates

Current `rag_config` presets are in-memory. Keep that approach for now.

Create combined candidates conceptually like:

```text
retriever candidate + query transform type
```

Possible generated ids:

```text
cfg_query_transform__retriever_chunk_paragraph_1000_keyword__none
cfg_query_transform__retriever_chunk_paragraph_1000_keyword__rewrite
```

Do not build full config persistence yet.

### Step 3 - Reuse Parent Candidate Runtime Setup

Reuse the existing runtime chunking code in:

```text
app/services/experiment_service.py
```

Retriever candidates already carry `source_config_id` and parent artifact metadata in their `rag_config`. Query transform candidates should preserve those fields.

### Step 4 - Run Retrieval Metrics

Use existing retrieval metrics:

```text
Hit@k
Recall@k
Precision@k
MRR
Avg latency
```

Keep chunk stats in the metrics too, because the query transform candidate still depends on a retriever/chunking candidate.

### Step 5 - Frontend Output

The leaderboard should show:

```text
Rank
Chunking Config
Retriever
Hit@k
Recall
Precision
MRR
Latency
Chunk Count
Avg Chunk Size
Coverage
Score
Status
```

### Step 6 - Save Artifact

The query transform comparison must persist:

```text
phase_id = query_transform_evaluation
input artifact = latest retriever_evaluation artifact id
kept_config_ids = top 5 query transform candidates
```

The artifact schema already supports `parent_artifact_id` and `parent_phase_id`.

Keep it local JSON. Do not add a production database yet.

## What Not To Do Yet

Do not implement these yet:

```text
LLM semantic chunking
GraphRAG
Agentic RAG
Answer evaluation
LLM-as-judge
Auth
Production database
Deployment
Full config database
```

LLM chunking is planned later because it needs:

```text
cost control
rate limit handling
retry
cache
async progress
```

## Quality Bar

The next AI must:

- Explain in Vietnamese.
- Read checklist/current phase before editing.
- Keep changes small and testable.
- Preserve existing keyword baseline.
- Preserve local JSON storage.
- Run `uv run python -m compileall app`.
- Run `npm run build` in `frontend`.
- Smoke test the relevant endpoint after changes.
- Update docs/checklist only when the feature actually works.
