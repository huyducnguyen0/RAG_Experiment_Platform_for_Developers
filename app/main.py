from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Agentic Research OS")


class ChatRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "message": "Agentic Research OS is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/chat")
def chat(request: ChatRequest):
    return {
        "answer": f"You asked: {request.question}"
    }
