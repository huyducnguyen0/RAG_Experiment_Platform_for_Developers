import type {
  DeleteDocumentResponse,
  DocumentDetail,
  DocumentSummary,
  HealthResponse,
  ResearchQueryRequest,
  ResearchQueryResponse,
} from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export async function fetchHealth(): Promise<HealthResponse> {
  return request('/health')
}

export async function listDocuments(): Promise<DocumentSummary[]> {
  return request('/documents')
}

export async function fetchDocument(documentId: string): Promise<DocumentDetail> {
  return request(`/documents/${documentId}`)
}

export async function uploadDocument(file: File): Promise<DocumentDetail> {
  const formData = new FormData()
  formData.append('file', file)

  return request('/documents/upload', {
    method: 'POST',
    body: formData,
  })
}

export async function deleteDocument(documentId: string): Promise<DeleteDocumentResponse> {
  return request(`/documents/${documentId}`, {
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
