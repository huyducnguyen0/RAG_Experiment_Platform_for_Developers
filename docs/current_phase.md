# Current Phase

Current phase: Phase 12 / Eval 7 - Multi-Phase RAG Experiment Pipeline

Current goal:
Stabilize the evaluation core of the platform so golden questions, experiments, and reports form one reliable workflow.

Current constraints:
- Keep keyword baseline as the baseline reference.
- Keep workspace data local persistent storage.
- No production database migration.
- Do not jump to answer-level evaluation before retrieval evaluation is trustworthy.

Current staged plan:
- Stage 1 - Golden dataset preparation
  - make sample documents upload-friendly
  - make corpus folders upload-friendly
  - make golden question files upload-friendly
  - reduce manual work for chunk-id mapping
- Stage 2 - Golden dataset validation
  - ensure uploaded golden questions point to real chunk ids
  - make validation and error messages clear
- Stage 3 - Workspace experiments
  - run experiments from workspace data
  - save run JSON and report markdown
  - expose run history and run detail APIs
- Stage 4 - Report quality
  - make reports useful for debugging failed retrieval cases
  - include enough metadata to understand each run
- Stage 5 - Strategy comparison
  - compare `keyword`, `vector`, and `hybrid` on the same workspace dataset
  - inspect metric differences and failure cases
- Stage 6 - RAG phase leaderboard
  - treat the current comparisons as `chunking_evaluation` and `retriever_evaluation`
  - show leaderboard output after pressing compare/test
  - keep a candidate pool instead of cutting directly to top 5
- Stage 7 - Multi-phase RAG experiment pipeline
  - evaluate chunking, retriever, query transform, reranker, context builder, and final answer quality as separate phases
  - prune candidates gradually across phases
  - export final top 5 only at the end

Current checklist focus:
- Phase 12 / Eval 1 - Golden Dataset Preparation
- Phase 12 / Eval 2 - Golden Dataset Validation
- Phase 12 / Eval 4 - Workspace Experiments
- Phase 12 / Eval 6 - Strategy Comparison
- Phase 12 / Eval 7 - Multi-Phase RAG Experiment Pipeline

Next concrete tasks:
- Confirm list/delete APIs work for golden questions from the frontend.
- Start modeling phase-specific experiment inputs for chunking, retriever, query transform, reranker, context builder, and final answer quality.
- Use the latest `retriever_evaluation` artifact as the input candidate pool for the next planned phase later.
- Add query transform evaluation phase after retriever artifacts are stable.

Expected behavior:
- Swagger exposes:
  - POST /workspaces/{workspace_id}/eval/questions/upload
  - GET /workspaces/{workspace_id}/eval/questions
  - DELETE /workspaces/{workspace_id}/eval/questions/{question_id}
  - GET /workspaces/{workspace_id}/rag-configs
  - GET /workspaces/{workspace_id}/rag-phases
  - GET /workspaces/{workspace_id}/phase-artifacts
  - GET /workspaces/{workspace_id}/phase-artifacts/latest
  - GET /workspaces/{workspace_id}/phase-artifacts/{artifact_id}
  - POST /workspaces/{workspace_id}/experiments/run
  - POST /workspaces/{workspace_id}/experiments/compare
  - GET /workspaces/{workspace_id}/experiments
  - GET /workspaces/{workspace_id}/experiments/{run_id}
  - GET /workspaces/{workspace_id}/reports/{run_id}
- Frontend allows:
  - document upload for one workspace
  - folder/corpus upload for nested `.txt` and `.md` files
  - golden question upload for one workspace
  - running `keyword`, `vector`, and `hybrid` experiments
  - selecting an active RAG phase before running or comparing experiments
  - running `chunking_evaluation` across fixed, paragraph, and recursive chunking candidates
  - running recursive character chunking candidates
  - viewing chunk count, average chunk size, and coverage metrics
  - selecting a first-class `rag_config` preset for a single experiment
  - comparing baseline `rag_config` presets in one action
  - viewing the latest persisted phase artifact after compare
  - running `retriever_evaluation` from the latest kept `chunking_evaluation` artifact
  - viewing a leaderboard table with score, rank, and candidate-pool status
  - viewing side-by-side question-level comparison across `keyword`, `vector`, and `hybrid`
  - reading saved reports

Product plan:
- `docs/rag_experiment_product_plan.md`

Project memory docs:
- `docs/codebase_status.md`
- `docs/feature_status.md`
- `docs/architecture_snapshot.md`
- `docs/next_chat_handoff.md`
