export type HealthResponse = {
  status: string
}

export type DocumentChunk = {
  chunk_id: string
  document_id: string
  chunk_index: number
  content: string
  start_index: number
  end_index: number
  content_length: number
}

export type DocumentSummary = {
  id: string
  workspace_id?: string | null
  title: string
  file_name: string
  file_type: string
  content_length: number
  chunk_count: number
  created_at: string
}

export type DocumentDetail = DocumentSummary & {
  content: string
  chunks: DocumentChunk[]
}

export type DeleteDocumentResponse = {
  deleted: boolean
  document_id: string
}

export type WorkspaceSummary = {
  id: string
  name: string
  created_at: string
  document_count: number
}

export type WorkspaceDetail = WorkspaceSummary & {
  document_ids: string[]
}

export type DeleteWorkspaceResponse = {
  deleted: boolean
  workspace_id: string
}

export type ResearchQueryRequest = {
  question: string
  top_k: number
}

export type ResearchSource = {
  document_id: string
  document_title: string
  chunk_id: string
  chunk_index: number
  score: number
  preview: string
}

export type ResearchQueryResponse = {
  answer: string
  sources: ResearchSource[]
  mode: string
}

export type EvalQuestion = {
  id: string
  question: string
  workspace_id: string
  expected_chunk_ids: string[]
  top_k: number
  notes: string
}

export type EvalQuestionListResponse = {
  items: EvalQuestion[]
  total: number
}

export type EvalQuestionUploadResponse = {
  workspace_id: string
  imported: number
}

export type DeleteEvalQuestionResponse = {
  deleted: boolean
  workspace_id: string
  question_id: string
}
