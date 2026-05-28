from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router

app = FastAPI(title="Agentic Research OS")

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(documents_router)


@app.get("/")
def root():
    return {
        "message": "Agentic Research OS is running"
    }
