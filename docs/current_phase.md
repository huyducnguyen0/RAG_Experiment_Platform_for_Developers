# Current Phase

Current phase: Phase Eval 4 - Workspace Experiments and Reports

Current goal:
Run keyword baseline experiments per workspace and expose run history + report retrieval APIs.

Current constraints:
- Keep keyword baseline as-is (no vector/hybrid/rerank yet).
- Keep workspace data local persistent storage.
- No production database migration.

Next task:
- Move to Phase Vector 1:
  - add vector retrieval strategy
  - run comparative eval between keyword and vector

Expected behavior:
- Swagger exposes:
  - POST /workspaces/{workspace_id}/experiments/run
  - GET /workspaces/{workspace_id}/experiments
  - GET /workspaces/{workspace_id}/experiments/{run_id}
  - GET /workspaces/{workspace_id}/reports/{run_id}

Project memory docs:
- `docs/codebase_status.md`
- `docs/feature_status.md`
- `docs/architecture_snapshot.md`
- `docs/next_chat_handoff.md`
