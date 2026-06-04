from __future__ import annotations

from fastapi import HTTPException

from app.schemas.rag_phase import RagPhase

DEFAULT_RAG_PHASE_ID = "retriever_evaluation"


def list_rag_phases(workspace_id: str | None = None) -> list[RagPhase]:
    _ = workspace_id
    return [
        RagPhase(
            phase_id="baseline_sanity",
            name="Baseline Sanity",
            description="Confirm the evaluation loop works before deeper RAG experiments.",
            status="planned",
            enabled=False,
            order=0,
        ),
        RagPhase(
            phase_id="chunking_evaluation",
            name="Chunking Evaluation",
            description="Compare chunking strategies before testing advanced retrieval modules.",
            status="active",
            enabled=True,
            order=1,
        ),
        RagPhase(
            phase_id="retriever_evaluation",
            name="Retriever Evaluation",
            description="Compare keyword, vector, and hybrid retrieval on the same golden set.",
            status="active",
            enabled=True,
            order=2,
        ),
        RagPhase(
            phase_id="query_transform_evaluation",
            name="Query Transform Evaluation",
            description="Test query rewrite, expansion, multi-query, and HyDE candidates.",
            status="planned",
            enabled=False,
            order=3,
        ),
        RagPhase(
            phase_id="reranker_evaluation",
            name="Reranker Evaluation",
            description="Measure reranking quality and latency after first-stage retrieval.",
            status="planned",
            enabled=False,
            order=4,
        ),
        RagPhase(
            phase_id="context_builder_evaluation",
            name="Context Builder Evaluation",
            description="Compare how retrieved chunks are assembled into final LLM context.",
            status="planned",
            enabled=False,
            order=5,
        ),
        RagPhase(
            phase_id="answer_evaluation",
            name="End-to-End Answer Evaluation",
            description="Evaluate answer correctness and faithfulness after retrieval is stable.",
            status="planned",
            enabled=False,
            order=6,
        ),
    ]


def get_rag_phase(phase_id: str, workspace_id: str | None = None) -> RagPhase:
    selected_phase_id = phase_id.strip().lower()
    for phase in list_rag_phases(workspace_id=workspace_id):
        if phase.phase_id == selected_phase_id:
            return phase

    allowed = ", ".join(phase.phase_id for phase in list_rag_phases(workspace_id=workspace_id))
    raise HTTPException(status_code=400, detail=f"Unsupported RAG phase. Allowed: {allowed}")


def validate_enabled_rag_phase(phase_id: str, workspace_id: str | None = None) -> RagPhase:
    phase = get_rag_phase(phase_id=phase_id, workspace_id=workspace_id)
    if not phase.enabled:
        raise HTTPException(
            status_code=400,
            detail=f"RAG phase '{phase.phase_id}' is {phase.status} and is not runnable yet.",
        )
    return phase
