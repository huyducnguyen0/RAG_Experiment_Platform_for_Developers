from app.schemas.chat import ChatResponse


def generate_answer(question: str) -> ChatResponse:
    return ChatResponse(
        answer=f"This is a mock answer for: {question}",
        mode="mock",
    )
