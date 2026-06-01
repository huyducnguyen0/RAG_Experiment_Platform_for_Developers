# Current Phase

Current phase: Phase Eval 4 - Workspace Experiments and Reports

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

Current checklist focus:
- Phase 12 / Eval 1 - Golden Dataset Preparation
- Phase 12 / Eval 2 - Golden Dataset Validation
- Phase 12 / Eval 4 - Workspace Experiments
- Phase 12 / Eval 6 - Strategy Comparison

Next concrete tasks:
- Confirm list/delete APIs work for golden questions from the frontend.
- Inspect cross-strategy failed cases and find where `keyword`, `vector`, or `hybrid` wins.
- Improve reports so side-by-side strategy differences are easier to read.

Expected behavior:
- Swagger exposes:
  - POST /workspaces/{workspace_id}/eval/questions/upload
  - GET /workspaces/{workspace_id}/eval/questions
  - DELETE /workspaces/{workspace_id}/eval/questions/{question_id}
  - POST /workspaces/{workspace_id}/experiments/run
  - POST /workspaces/{workspace_id}/experiments/compare
  - GET /workspaces/{workspace_id}/experiments
  - GET /workspaces/{workspace_id}/experiments/{run_id}
  - GET /workspaces/{workspace_id}/reports/{run_id}
- Frontend allows:
  - document upload for one workspace
  - golden question upload for one workspace
  - running `keyword`, `vector`, and `hybrid` experiments
  - comparing `keyword`, `vector`, and `hybrid` in one action
  - reading saved reports

Project memory docs:
- `docs/codebase_status.md`
- `docs/feature_status.md`
- `docs/architecture_snapshot.md`
- `docs/next_chat_handoff.md`
