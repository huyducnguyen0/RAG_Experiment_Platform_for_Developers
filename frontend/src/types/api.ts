export type HealthResponse = {
  status: string
}

export type DocumentChunk = {
  chunk_id: string
  document_id: string
  chunk_index: number
  content: string
  original_text: string
  headline: string
  summary: string
  start_index: number
  end_index: number
  content_length: number
  source_path: string
  relative_path: string
  folder_path: string
  doc_type: string
  file_extension: string
  chunking_strategy: string
  chunk_size: number
  chunk_overlap: number
}

export type DocumentSummary = {
  id: string
  workspace_id?: string | null
  title: string
  file_name: string
  file_type: string
  source_path: string
  relative_path: string
  folder_path: string
  doc_type: string
  file_extension: string
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

export type FolderUploadResponse = {
  workspace_id: string
  imported: number
  skipped: number
  documents: DocumentSummary[]
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
  reference_answer: string
  keywords: string[]
  category: string
  gold_evidence_text: string
  label_type: string
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

export type RagConfigComponent = {
  type: string
  params: Record<string, string | number | boolean>
}

export type RagConfigPreset = {
  config_id: string
  name: string
  description: string
  rag_stage: string
  strategy: string
  top_k: number
  chunking: RagConfigComponent
  retriever: RagConfigComponent
  query_transform: RagConfigComponent
  reranker: RagConfigComponent
  context_builder: RagConfigComponent
}

export type RagConfigListResponse = {
  items: RagConfigPreset[]
  total: number
}

export type RagPhase = {
  phase_id: string
  name: string
  description: string
  status: string
  enabled: boolean
  order: number
}

export type RagPhaseListResponse = {
  items: RagPhase[]
  total: number
}

export type PhaseArtifactCandidate = {
  rank: number
  run_id: string
  config_id: string
  config_name: string
  strategy: string
  chunking_type: string
  chunking_params: Record<string, string | number | boolean>
  retriever_type: string
  score: number
  status: string
  verdict: string
  hit_at_k: number
  recall_at_k: number
  precision_at_k: number
  mrr: number
  avg_latency_ms: number
  chunk_count: number
  avg_chunk_size: number
  min_chunk_size: number
  max_chunk_size: number
  coverage_ratio: number
}

export type PhaseArtifact = {
  artifact_id: string
  workspace_id: string
  phase_id: string
  parent_artifact_id: string | null
  parent_phase_id: string | null
  created_at: string
  candidate_pool_size: number
  total_candidates: number
  kept_count: number
  input_config_ids: string[]
  kept_config_ids: string[]
  pruned_config_ids: string[]
  best_config_id: string | null
  best_config_name: string | null
  candidates: PhaseArtifactCandidate[]
  summary: Record<string, unknown>
}

export type PhaseArtifactListResponse = {
  items: PhaseArtifact[]
  total: number
}

export type ExperimentMetrics = {
  case_count: number
  hit_count: number
  hit_at_k: number
  recall_at_k: number
  precision_at_k: number
  mrr: number
  avg_latency_ms: number
  chunk_count: number
  avg_chunk_size: number
  min_chunk_size: number
  max_chunk_size: number
  coverage_ratio: number
}

export type ExperimentCaseResult = {
  question_id: string
  question: string
  workspace_id: string
  top_k: number
  notes: string
  expected_chunk_ids: string[]
  returned_chunk_ids: string[]
  returned_source_paths: string[]
  returned_doc_types: string[]
  label_type: string
  relevant_count: number
  hit: boolean
  recall_at_k: number
  precision_at_k: number
  reciprocal_rank: number
  latency_ms: number
}

export type ExperimentRunResponse = {
  run_id: string
  workspace_id: string
  config_id: string
  config_name: string
  rag_stage: string
  strategy: string
  top_k: number
  created_at: string
  metrics: ExperimentMetrics
  results: ExperimentCaseResult[]
  report_markdown_path: string
  rag_config: RagConfigPreset | null
}

export type ExperimentSummary = {
  run_id: string
  workspace_id: string
  config_id: string
  config_name: string
  rag_stage: string
  strategy: string
  top_k: number
  created_at: string
  metrics: ExperimentMetrics
  rag_config: RagConfigPreset | null
}

export type ExperimentListResponse = {
  items: ExperimentSummary[]
  total: number
}

export type ExperimentReportResponse = {
  run_id: string
  workspace_id: string
  markdown: string
}

export type ExperimentLeaderboardRow = {
  rank: number
  run_id: string
  config_id: string
  config_name: string
  rag_stage: string
  strategy: string
  metrics: ExperimentMetrics
  score: number
  status: string
  verdict: string
  rag_config: RagConfigPreset | null
}

export type ExperimentStrategyQuestionResult = {
  config_id: string
  config_name: string
  strategy: string
  run_id: string
  hit: boolean
  returned_chunk_ids: string[]
  relevant_count: number
  recall_at_k: number
  precision_at_k: number
  reciprocal_rank: number
  latency_ms: number
}

export type ExperimentQuestionComparisonRow = {
  question_id: string
  question: string
  expected_chunk_ids: string[]
  notes: string
  winner: string | null
  status: string
  strategy_results: ExperimentStrategyQuestionResult[]
}

export type ExperimentComparisonSummary = {
  stage: string
  total_configs: number
  candidate_pool_size: number
  kept_count: number
  best_config_id: string | null
  best_config_name: string | null
  fastest_config_name: string | null
  highest_recall_config_name: string | null
  recommendation: string
}

export type ExperimentComparisonResponse = {
  workspace_id: string
  stage: string
  top_k: number
  created_at: string
  best_strategy: string | null
  summary: ExperimentComparisonSummary
  phase_artifact: PhaseArtifact | null
  leaderboard: ExperimentLeaderboardRow[]
  rag_configs: RagConfigPreset[]
  question_comparisons: ExperimentQuestionComparisonRow[]
  runs: ExperimentSummary[]
}
