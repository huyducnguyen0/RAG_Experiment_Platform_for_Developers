from fastapi import APIRouter

from app.schemas.research import RetrieveRequest, RetrieveResponse
from app.services.retrieval_service import retrieve_relevant_chunks

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest):
    return retrieve_relevant_chunks(
        question=request.question,
        top_k=request.top_k,
    )
