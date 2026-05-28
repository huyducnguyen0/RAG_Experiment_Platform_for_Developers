# Current Phase

Current phase: Phase W4 - Workspace Chat Panel

Current goal:
Turn the workspace query area into a lightweight chat-style panel per workspace.

Current constraints:
- Do not add vector database yet.
- Do not add production database yet.
- Keep workspace data local for the MVP.
- Do not add auth or persistent chat history yet.

Next task:
Add local chat messages in the frontend:
- User messages are stored in React state.
- Assistant messages come from POST /workspaces/{workspace_id}/research/query.
- Sources stay attached to assistant messages.
- Switching workspace resets or scopes the visible chat.

Expected behavior:
- Each workspace has its own documents and query context.
- The UI feels closer to NotebookLM while staying simple.
- No backend chat memory is required yet.
