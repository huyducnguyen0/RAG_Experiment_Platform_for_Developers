from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import generate_answer

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return generate_answer(request.question)
