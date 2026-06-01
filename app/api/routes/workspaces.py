from fastapi import APIRouter, File, UploadFile

from app.schemas.document import (
    DeleteDocumentResponse,
    DocumentDetail,
    DocumentSummary,
)
from app.schemas.experiment import (
    ExperimentCompareRequest,
    ExperimentComparisonResponse,
    ExperimentListResponse,
    ExperimentReportResponse,
    ExperimentRunRequest,
    ExperimentRunResponse,
)
from app.schemas.eval import (
    DeleteEvalQuestionResponse,
    EvalQuestionListResponse,
    EvalQuestionUploadResponse,
)
from app.schemas.research import (
    ResearchQueryRequest,
    ResearchQueryResponse,
    RetrieveRequest,
    RetrieveResponse,
)
from app.schemas.workspace import (
    DeleteWorkspaceResponse,
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspaceSummary,
    WorkspaceUpdate,
)
from app.services.document_service import (
    delete_document,
    get_document,
    list_documents,
    save_uploaded_document,
)
from app.services.eval_question_service import (
    delete_eval_question,
    list_eval_questions,
    upload_eval_questions_file,
)
from app.services.experiment_service import (
    get_workspace_experiment,
    get_workspace_report_markdown,
    list_workspace_experiments,
    run_workspace_experiment_comparison,
    run_workspace_experiment,
)
from app.services.rag_service import answer_research_query
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.workspace_service import (
    create_workspace,
    delete_workspace,
    ensure_workspace_exists,
    get_workspace,
    list_workspaces,
    rename_workspace,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceDetail)
def create_new_workspace(request: WorkspaceCreate):
    return create_workspace(request.name)


@router.get("", response_model=list[WorkspaceSummary])
def get_workspaces():
    return list_workspaces()


@router.get("/{workspace_id}", response_model=WorkspaceDetail)
def get_workspace_detail(workspace_id: str):
    return get_workspace(workspace_id)


@router.patch("/{workspace_id}", response_model=WorkspaceDetail)
def update_workspace(workspace_id: str, request: WorkspaceUpdate):
    return rename_workspace(workspace_id, request.name)


@router.delete("/{workspace_id}", response_model=DeleteWorkspaceResponse)
def remove_workspace(workspace_id: str):
    delete_workspace(workspace_id)
    return DeleteWorkspaceResponse(deleted=True, workspace_id=workspace_id)


@router.post("/{workspace_id}/documents/upload", response_model=DocumentDetail)
def upload_workspace_document(
    workspace_id: str,
    file: UploadFile = File(...),
):
    ensure_workspace_exists(workspace_id)
    return save_uploaded_document(file, workspace_id=workspace_id)


@router.get("/{workspace_id}/documents", response_model=list[DocumentSummary])
def get_workspace_documents(workspace_id: str):
    ensure_workspace_exists(workspace_id)
    return list_documents(workspace_id=workspace_id)


@router.get("/{workspace_id}/documents/{document_id}", response_model=DocumentDetail)
def get_workspace_document_detail(workspace_id: str, document_id: str):
    ensure_workspace_exists(workspace_id)
    return get_document(document_id, workspace_id=workspace_id)


@router.delete(
    "/{workspace_id}/documents/{document_id}",
    response_model=DeleteDocumentResponse,
)
def remove_workspace_document(workspace_id: str, document_id: str):
    ensure_workspace_exists(workspace_id)
    delete_document(document_id, workspace_id=workspace_id)
    return DeleteDocumentResponse(deleted=True, document_id=document_id)


@router.post("/{workspace_id}/research/retrieve", response_model=RetrieveResponse)
def retrieve_from_workspace(workspace_id: str, request: RetrieveRequest):
    ensure_workspace_exists(workspace_id)
    return retrieve_relevant_chunks(
        question=request.question,
        top_k=request.top_k,
        workspace_id=workspace_id,
    )


@router.post("/{workspace_id}/research/query", response_model=ResearchQueryResponse)
def query_workspace(workspace_id: str, request: ResearchQueryRequest):
    ensure_workspace_exists(workspace_id)
    return answer_research_query(
        question=request.question,
        top_k=request.top_k,
        workspace_id=workspace_id,
    )


@router.post(
    "/{workspace_id}/eval/questions/upload",
    response_model=EvalQuestionUploadResponse,
)
def upload_workspace_eval_questions(
    workspace_id: str,
    file: UploadFile = File(...),
):
    ensure_workspace_exists(workspace_id)
    imported = upload_eval_questions_file(workspace_id=workspace_id, upload_file=file)
    return EvalQuestionUploadResponse(workspace_id=workspace_id, imported=imported)


@router.get(
    "/{workspace_id}/eval/questions",
    response_model=EvalQuestionListResponse,
)
def get_workspace_eval_questions(workspace_id: str):
    ensure_workspace_exists(workspace_id)
    items = list_eval_questions(workspace_id=workspace_id)
    return EvalQuestionListResponse(items=items, total=len(items))


@router.delete(
    "/{workspace_id}/eval/questions/{question_id}",
    response_model=DeleteEvalQuestionResponse,
)
def remove_workspace_eval_question(workspace_id: str, question_id: str):
    ensure_workspace_exists(workspace_id)
    delete_eval_question(workspace_id=workspace_id, question_id=question_id)
    return DeleteEvalQuestionResponse(
        deleted=True,
        workspace_id=workspace_id,
        question_id=question_id,
    )


@router.post(
    "/{workspace_id}/experiments/run",
    response_model=ExperimentRunResponse,
)
def run_workspace_experiment_route(workspace_id: str, request: ExperimentRunRequest):
    ensure_workspace_exists(workspace_id)
    return run_workspace_experiment(
        workspace_id=workspace_id,
        strategy=request.strategy,
        top_k=request.top_k,
    )


@router.post(
    "/{workspace_id}/experiments/compare",
    response_model=ExperimentComparisonResponse,
)
def compare_workspace_experiments_route(workspace_id: str, request: ExperimentCompareRequest):
    ensure_workspace_exists(workspace_id)
    return run_workspace_experiment_comparison(
        workspace_id=workspace_id,
        strategies=request.strategies,
        top_k=request.top_k,
    )


@router.get(
    "/{workspace_id}/experiments",
    response_model=ExperimentListResponse,
)
def list_workspace_experiments_route(workspace_id: str):
    ensure_workspace_exists(workspace_id)
    items = list_workspace_experiments(workspace_id=workspace_id)
    return ExperimentListResponse(items=items, total=len(items))


@router.get(
    "/{workspace_id}/experiments/{run_id}",
    response_model=ExperimentRunResponse,
)
def get_workspace_experiment_route(workspace_id: str, run_id: str):
    ensure_workspace_exists(workspace_id)
    return get_workspace_experiment(workspace_id=workspace_id, run_id=run_id)


@router.get(
    "/{workspace_id}/reports/{run_id}",
    response_model=ExperimentReportResponse,
)
def get_workspace_report_route(workspace_id: str, run_id: str):
    ensure_workspace_exists(workspace_id)
    markdown = get_workspace_report_markdown(workspace_id=workspace_id, run_id=run_id)
    return ExperimentReportResponse(
        run_id=run_id,
        workspace_id=workspace_id,
        markdown=markdown,
    )
