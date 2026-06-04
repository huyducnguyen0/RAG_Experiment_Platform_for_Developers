INSUFFICIENT_CONTEXT_ANSWER = (
    "The available documents do not contain enough information to answer "
    "this question."
)


def generate_mock_answer(question: str, context: str) -> str:
    if not context.strip():
        return INSUFFICIENT_CONTEXT_ANSWER

    return (
        "Based on the retrieved document context, here is a mock research "
        f"answer for: {question}\n\n"
        f"Context used:\n{context}"
    )
