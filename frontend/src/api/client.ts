import type {
  DeleteEvalQuestionResponse,
  DeleteDocumentResponse,
  DeleteWorkspaceResponse,
  DocumentDetail,
  DocumentSummary,
  EvalQuestionListResponse,
  EvalQuestionUploadResponse,
  ExperimentListResponse,
  ExperimentReportResponse,
  ExperimentRunResponse,
  HealthResponse,
  ResearchQueryRequest,
  ResearchQueryResponse,
  WorkspaceDetail,
  WorkspaceSummary,
} from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export async function fetchHealth(): Promise<HealthResponse> {
  return request('/health')
}

export async function listDocuments(): Promise<DocumentSummary[]> {
  return request('/documents')
}

export async function listWorkspaces(): Promise<WorkspaceSummary[]> {
  return request('/workspaces')
}

export async function createWorkspace(name: string): Promise<WorkspaceDetail> {
  return request('/workspaces', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name }),
  })
}

export async function renameWorkspace(
  workspaceId: string,
  name: string,
): Promise<WorkspaceDetail> {
  return request(`/workspaces/${workspaceId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name }),
  })
}

export async function deleteWorkspace(workspaceId: string): Promise<DeleteWorkspaceResponse> {
  return request(`/workspaces/${workspaceId}`, {
    method: 'DELETE',
  })
}

export async function fetchDocument(documentId: string): Promise<DocumentDetail> {
  return request(`/documents/${documentId}`)
}

export async function listWorkspaceDocuments(workspaceId: string): Promise<DocumentSummary[]> {
  return request(`/workspaces/${workspaceId}/documents`)
}

export async function fetchWorkspaceDocument(
  workspaceId: string,
  documentId: string,
): Promise<DocumentDetail> {
  return request(`/workspaces/${workspaceId}/documents/${documentId}`)
}

export async function uploadDocument(file: File): Promise<DocumentDetail> {
  const formData = new FormData()
  formData.append('file', file)

  return request('/documents/upload', {
    method: 'POST',
    body: formData,
  })
}

export async function uploadWorkspaceDocument(
  workspaceId: string,
  file: File,
): Promise<DocumentDetail> {
  const formData = new FormData()
  formData.append('file', file)

  return request(`/workspaces/${workspaceId}/documents/upload`, {
    method: 'POST',
    body: formData,
  })
}

export async function deleteDocument(documentId: string): Promise<DeleteDocumentResponse> {
  return request(`/documents/${documentId}`, {
    method: 'DELETE',
  })
}

export async function deleteWorkspaceDocument(
  workspaceId: string,
  documentId: string,
): Promise<DeleteDocumentResponse> {
  return request(`/workspaces/${workspaceId}/documents/${documentId}`, {
    method: 'DELETE',
  })
}

export async function queryResearch(payload: ResearchQueryRequest): Promise<ResearchQueryResponse> {
  return request('/research/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export async function queryWorkspaceResearch(
  workspaceId: string,
  payload: ResearchQueryRequest,
): Promise<ResearchQueryResponse> {
  return request(`/workspaces/${workspaceId}/research/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export async function uploadWorkspaceEvalQuestions(
  workspaceId: string,
  file: File,
): Promise<EvalQuestionUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  return request(`/workspaces/${workspaceId}/eval/questions/upload`, {
    method: 'POST',
    body: formData,
  })
}

export async function listWorkspaceEvalQuestions(
  workspaceId: string,
): Promise<EvalQuestionListResponse> {
  return request(`/workspaces/${workspaceId}/eval/questions`)
}

export async function deleteWorkspaceEvalQuestion(
  workspaceId: string,
  questionId: string,
): Promise<DeleteEvalQuestionResponse> {
  return request(`/workspaces/${workspaceId}/eval/questions/${questionId}`, {
    method: 'DELETE',
  })
}

export async function runWorkspaceExperiment(
  workspaceId: string,
  payload: { strategy: string; top_k: number },
): Promise<ExperimentRunResponse> {
  return request(`/workspaces/${workspaceId}/experiments/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export async function listWorkspaceExperiments(
  workspaceId: string,
): Promise<ExperimentListResponse> {
  return request(`/workspaces/${workspaceId}/experiments`)
}

export async function getWorkspaceExperiment(
  workspaceId: string,
  runId: string,
): Promise<ExperimentRunResponse> {
  return request(`/workspaces/${workspaceId}/experiments/${runId}`)
}

export async function getWorkspaceReport(
  workspaceId: string,
  runId: string,
): Promise<ExperimentReportResponse> {
  return request(`/workspaces/${workspaceId}/reports/${runId}`)
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)

  if (!response.ok) {
    throw new Error(await getErrorDetail(response))
  }

  return response.json() as Promise<T>
}

async function getErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') {
      return body.detail
    }
  } catch {
    return `${response.status} ${response.statusText}`
  }

  return `${response.status} ${response.statusText}`
}
