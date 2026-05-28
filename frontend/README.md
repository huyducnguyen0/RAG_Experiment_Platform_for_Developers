# Agentic Research OS Frontend

React + Vite testing interface for the Agentic Research OS backend.

## Run

Start the backend first:

```bash
uv run uvicorn app.main:app --reload
```

Then start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

The frontend expects the backend at:

```text
http://127.0.0.1:8000
```

Override it with:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```
