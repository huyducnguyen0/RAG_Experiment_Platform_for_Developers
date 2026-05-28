# Current Phase

Current phase: Phase Eval 3 - Golden Questions API

Current goal:
Add workspace-level Golden Questions upload/list/delete APIs for evaluation workflows.

Current constraints:
- Keep keyword baseline as-is (no vector/hybrid/rerank yet).
- Keep workspace data local persistent storage.
- No production database migration.

Next task:
- Move to Phase Eval 3:
  - wire frontend Golden Questions tab to upload/list/delete
  - add experiments run/list/detail APIs

Expected behavior:
- Swagger exposes:
  - POST /workspaces/{workspace_id}/eval/questions/upload
  - GET /workspaces/{workspace_id}/eval/questions
  - DELETE /workspaces/{workspace_id}/eval/questions/{question_id}
