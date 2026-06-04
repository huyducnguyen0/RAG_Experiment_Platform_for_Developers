import { useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  Activity,
  AlertCircle,
  Beaker,
  FileText,
  FolderOpen,
  Loader2,
  MessageSquare,
  Plus,
  RefreshCcw,
  Search,
  Sparkles,
  Trash2,
  Upload,
} from 'lucide-react'
import {
  compareWorkspaceExperiments,
  createWorkspace,
  deleteWorkspace,
  deleteWorkspaceDocument,
  deleteWorkspaceEvalQuestion,
  fetchHealth,
  getLatestWorkspacePhaseArtifact,
  getWorkspaceExperiment,
  getWorkspaceReport,
  listWorkspaceExperiments,
  fetchWorkspaceDocument,
  listWorkspaceDocuments,
  listWorkspaceEvalQuestions,
  listWorkspaceRagConfigs,
  listWorkspaceRagPhases,
  listWorkspaces,
  queryWorkspaceResearch,
  runWorkspaceExperiment,
  uploadWorkspaceDocument,
  uploadWorkspaceDocumentFolder,
  uploadWorkspaceEvalQuestions,
} from './api/client'
import type {
  DocumentDetail,
  DocumentSummary,
  EvalQuestion,
  ExperimentComparisonResponse,
  ExperimentQuestionComparisonRow,
  ExperimentReportResponse,
  ExperimentRunResponse,
  ExperimentStrategyQuestionResult,
  ExperimentSummary,
  PhaseArtifact,
  RagConfigPreset,
  RagPhase,
  ResearchQueryResponse,
  WorkspaceSummary,
} from './types/api'

type HealthState = 'checking' | 'online' | 'offline'
type WorkspaceTab = 'documents' | 'golden' | 'experiments' | 'reports' | 'playground'
type RetrievalStrategy = 'keyword' | 'vector' | 'hybrid'
type QuestionComparisonFilter =
  | 'all'
  | 'all_failed'
  | 'partial_hit'
  | 'all_hit'
  | 'winner_keyword'
  | 'winner_vector'
  | 'winner_hybrid'
type AnswerReviewFilter = 'all' | 'with_reference' | 'low_match' | 'high_match'

const DEFAULT_RAG_CONFIG_ID = 'cfg_keyword_baseline'
const DEFAULT_RAG_PHASE_ID = 'retriever_evaluation'

function App() {
  const [health, setHealth] = useState<HealthState>('checking')
  const [notice, setNotice] = useState('')
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('documents')

  const [workspaces, setWorkspaces] = useState<WorkspaceSummary[]>([])
  const [workspaceName, setWorkspaceName] = useState('New RAG Experiment')
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState('')

  const [documents, setDocuments] = useState<DocumentSummary[]>([])
  const [selectedDocumentId, setSelectedDocumentId] = useState('')
  const [selectedDocument, setSelectedDocument] = useState<DocumentDetail | null>(null)

  const [evalQuestions, setEvalQuestions] = useState<EvalQuestion[]>([])
  const [ragConfigs, setRagConfigs] = useState<RagConfigPreset[]>([])
  const [selectedConfigId, setSelectedConfigId] = useState(DEFAULT_RAG_CONFIG_ID)
  const [ragPhases, setRagPhases] = useState<RagPhase[]>([])
  const [selectedPhaseId, setSelectedPhaseId] = useState(DEFAULT_RAG_PHASE_ID)
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([])
  const [selectedRun, setSelectedRun] = useState<ExperimentRunResponse | null>(null)
  const [selectedComparison, setSelectedComparison] = useState<ExperimentComparisonResponse | null>(null)
  const [latestPhaseArtifact, setLatestPhaseArtifact] = useState<PhaseArtifact | null>(null)
  const [selectedReport, setSelectedReport] = useState<ExperimentReportResponse | null>(null)
  const [question, setQuestion] = useState('What does this workspace say about FastAPI?')
  const [answer, setAnswer] = useState<ResearchQueryResponse | null>(null)

  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false)
  const [isDeletingWorkspace, setIsDeletingWorkspace] = useState(false)
  const [isLoadingWorkspace, setIsLoadingWorkspace] = useState(false)
  const [isUploadingDocument, setIsUploadingDocument] = useState(false)
  const [isUploadingEval, setIsUploadingEval] = useState(false)
  const [isRunningExperiment, setIsRunningExperiment] = useState(false)
  const [isLoadingReport, setIsLoadingReport] = useState(false)
  const [isLoadingDocument, setIsLoadingDocument] = useState(false)
  const [isQuerying, setIsQuerying] = useState(false)

  const selectedWorkspace = useMemo(
    () => workspaces.find((workspace) => workspace.id === selectedWorkspaceId),
    [workspaces, selectedWorkspaceId],
  )
  const weakLabelEvalQuestions = useMemo(
    () => evalQuestions.filter((item) => item.label_type !== 'strong_chunk_ids'),
    [evalQuestions],
  )

  async function refreshHealth() {
    setHealth('checking')
    try {
      await fetchHealth()
      setHealth('online')
    } catch {
      setHealth('offline')
    }
  }

  async function refreshWorkspaces(nextWorkspaceId?: string) {
    const items = await listWorkspaces()
    setWorkspaces(items)

    if (nextWorkspaceId) {
      await selectWorkspace(nextWorkspaceId, items)
      return
    }

    if (selectedWorkspaceId && !items.some((item) => item.id === selectedWorkspaceId)) {
      closeWorkspace()
    }
  }

  async function selectWorkspace(workspaceId: string, cached?: WorkspaceSummary[]) {
    setSelectedWorkspaceId(workspaceId)
    setActiveTab('documents')
    setAnswer(null)

    if (!workspaceId) {
      setDocuments([])
      setEvalQuestions([])
      setRagConfigs([])
      setSelectedConfigId(DEFAULT_RAG_CONFIG_ID)
      setRagPhases([])
      setSelectedPhaseId(DEFAULT_RAG_PHASE_ID)
      setLatestPhaseArtifact(null)
      setSelectedDocumentId('')
      setSelectedDocument(null)
      return
    }

    setIsLoadingWorkspace(true)
    try {
      const [
        workspaceDocuments,
        workspaceEval,
        workspaceRagConfigs,
        workspaceRagPhases,
      ] = await Promise.all([
        listWorkspaceDocuments(workspaceId),
        listWorkspaceEvalQuestions(workspaceId),
        listWorkspaceRagConfigs(workspaceId),
        listWorkspaceRagPhases(workspaceId),
      ])
      const activePhaseId = firstEnabledPhaseId(workspaceRagPhases.items)
      const phaseConfigId =
        workspaceRagConfigs.items.find((config) => config.rag_stage === activePhaseId)?.config_id ??
        workspaceRagConfigs.items[0]?.config_id ??
        DEFAULT_RAG_CONFIG_ID
      setDocuments(workspaceDocuments)
      setEvalQuestions(workspaceEval.items)
      setRagConfigs(workspaceRagConfigs.items)
      setSelectedConfigId(phaseConfigId)
      setRagPhases(workspaceRagPhases.items)
      setSelectedPhaseId(activePhaseId)
      setLatestPhaseArtifact(await getLatestWorkspacePhaseArtifact(workspaceId, activePhaseId).catch(() => null))
      if (workspaceDocuments.length > 0) {
        await selectDocument(workspaceId, workspaceDocuments[0].id)
      } else {
        setSelectedDocumentId('')
        setSelectedDocument(null)
      }

      if (!cached) {
        const refreshed = await listWorkspaces()
        setWorkspaces(refreshed)
      }

      const experimentList = await listWorkspaceExperiments(workspaceId)
      setExperiments(experimentList.items)
      setSelectedRun(null)
      setSelectedComparison(null)
      setSelectedReport(null)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsLoadingWorkspace(false)
    }
  }

  async function selectDocument(workspaceId: string, documentId: string) {
    setSelectedDocumentId(documentId)
    if (!workspaceId || !documentId) {
      setSelectedDocument(null)
      return
    }

    setIsLoadingDocument(true)
    try {
      const detail = await fetchWorkspaceDocument(workspaceId, documentId)
      setSelectedDocument(detail)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsLoadingDocument(false)
    }
  }

  async function handleCreateWorkspace() {
    setIsCreatingWorkspace(true)
    setNotice('')
    try {
      const created = await createWorkspace(workspaceName)
      setWorkspaceName('New RAG Experiment')
      await refreshWorkspaces(created.id)
      setNotice(`Created workspace ${created.name}`)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsCreatingWorkspace(false)
    }
  }

  async function handleDeleteWorkspace() {
    if (!selectedWorkspaceId) {
      return
    }

    const workspaceLabel = selectedWorkspace?.name ?? selectedWorkspaceId
    if (!window.confirm(`Delete workspace "${workspaceLabel}" and all data inside it?`)) {
      return
    }

    setIsDeletingWorkspace(true)
    setNotice('')
    try {
      await deleteWorkspace(selectedWorkspaceId)
      closeWorkspace()
      await refreshWorkspaces()
      setNotice(`Deleted workspace ${workspaceLabel}`)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsDeletingWorkspace(false)
    }
  }

  async function handleUploadDocuments(files: File[]) {
    if (!selectedWorkspaceId) {
      return
    }
    if (files.length === 0) {
      return
    }

    setIsUploadingDocument(true)
    setNotice('')
    try {
      let uploaded: DocumentDetail | null = null
      for (const file of files) {
        uploaded = await uploadWorkspaceDocument(selectedWorkspaceId, file)
      }
      const workspaceDocuments = await listWorkspaceDocuments(selectedWorkspaceId)
      setDocuments(workspaceDocuments)
      if (uploaded) {
        setSelectedDocumentId(uploaded.id)
        setSelectedDocument(uploaded)
      }
      await refreshWorkspaces(selectedWorkspaceId)
      setNotice(`Uploaded ${files.length} file(s)`)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsUploadingDocument(false)
    }
  }

  async function handleUploadDocumentFolder(files: File[]) {
    if (!selectedWorkspaceId) {
      return
    }
    if (files.length === 0) {
      return
    }

    setIsUploadingDocument(true)
    setNotice('')
    try {
      const validFiles = files.filter((file) => isSupportedDocumentFile(file))
      const result = await uploadWorkspaceDocumentFolder(selectedWorkspaceId, validFiles)
      const workspaceDocuments = await listWorkspaceDocuments(selectedWorkspaceId)
      setDocuments(workspaceDocuments)
      if (workspaceDocuments.length > 0) {
        await selectDocument(selectedWorkspaceId, workspaceDocuments[workspaceDocuments.length - 1].id)
      }
      await refreshWorkspaces(selectedWorkspaceId)
      setNotice(`Imported ${result.imported} file(s), skipped ${result.skipped + (files.length - validFiles.length)}`)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsUploadingDocument(false)
    }
  }

  async function handleDeleteDocument(documentId: string) {
    if (!selectedWorkspaceId) {
      return
    }

    setNotice('')
    try {
      await deleteWorkspaceDocument(selectedWorkspaceId, documentId)
      const workspaceDocuments = await listWorkspaceDocuments(selectedWorkspaceId)
      setDocuments(workspaceDocuments)
      if (workspaceDocuments.length > 0) {
        await selectDocument(selectedWorkspaceId, workspaceDocuments[0].id)
      } else {
        setSelectedDocumentId('')
        setSelectedDocument(null)
      }
      await refreshWorkspaces(selectedWorkspaceId)
      setNotice('Document deleted')
    } catch (error) {
      setNotice(getErrorMessage(error))
    }
  }

  async function handleUploadEval(file: File) {
    if (!selectedWorkspaceId) {
      return
    }

    setIsUploadingEval(true)
    setNotice('')
    try {
      const result = await uploadWorkspaceEvalQuestions(selectedWorkspaceId, file)
      const latest = await listWorkspaceEvalQuestions(selectedWorkspaceId)
      setEvalQuestions(latest.items)
      setNotice(`Imported ${result.imported} golden questions`)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsUploadingEval(false)
    }
  }

  async function handleDeleteEvalQuestion(questionId: string) {
    if (!selectedWorkspaceId) {
      return
    }

    setNotice('')
    try {
      await deleteWorkspaceEvalQuestion(selectedWorkspaceId, questionId)
      const latest = await listWorkspaceEvalQuestions(selectedWorkspaceId)
      setEvalQuestions(latest.items)
      setNotice('Golden question deleted')
    } catch (error) {
      setNotice(getErrorMessage(error))
    }
  }

  async function handleQuery() {
    if (!selectedWorkspaceId) {
      return
    }

    setIsQuerying(true)
    setNotice('')
    try {
      const result = await queryWorkspaceResearch(selectedWorkspaceId, {
        question,
        top_k: 5,
      })
      setAnswer(result)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsQuerying(false)
    }
  }

  function closeWorkspace() {
    setSelectedWorkspaceId('')
    setDocuments([])
    setEvalQuestions([])
    setRagConfigs([])
    setSelectedConfigId(DEFAULT_RAG_CONFIG_ID)
    setRagPhases([])
    setSelectedPhaseId(DEFAULT_RAG_PHASE_ID)
    setSelectedDocumentId('')
    setSelectedDocument(null)
    setExperiments([])
    setSelectedRun(null)
    setSelectedComparison(null)
    setLatestPhaseArtifact(null)
    setSelectedReport(null)
    setAnswer(null)
    setActiveTab('documents')
  }

  async function handleRunExperiment() {
    if (!selectedWorkspaceId) {
      return
    }

    setIsRunningExperiment(true)
    setNotice('')
    try {
      const selectedConfig = findRagConfig(ragConfigs, selectedConfigId)
      const run = await runWorkspaceExperiment(selectedWorkspaceId, {
        strategy: selectedConfig?.strategy ?? strategyFromConfigId(selectedConfigId),
        config_id: selectedConfigId,
        top_k: 5,
        stage: selectedPhaseId,
      })
      const latest = await listWorkspaceExperiments(selectedWorkspaceId)
      setExperiments(latest.items)
      setSelectedRun(run)
      setSelectedComparison(null)
      setActiveTab('experiments')
      setNotice(`Experiment ${run.run_id} completed with ${run.strategy}`)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsRunningExperiment(false)
    }
  }

  async function handleRunComparison() {
    if (!selectedWorkspaceId) {
      return
    }

    setIsRunningExperiment(true)
    setNotice('')
    try {
      const phaseConfigs = ragConfigs.filter((config) => config.rag_stage === selectedPhaseId)
      const comparisonConfigIds = phaseConfigs.map((config) => config.config_id)
      const comparisonStrategies =
        phaseConfigs.length > 0 ? phaseConfigs.map((config) => config.strategy) : ['keyword', 'vector', 'hybrid']
      const comparison = await compareWorkspaceExperiments(selectedWorkspaceId, {
        strategies: comparisonStrategies,
        config_ids: comparisonConfigIds.length > 0 ? comparisonConfigIds : undefined,
        top_k: 5,
        stage: selectedPhaseId,
        candidate_pool_size: selectedPhaseId === 'chunking_evaluation' ? 3 : 5,
      })
      const latest = await listWorkspaceExperiments(selectedWorkspaceId)
      setExperiments(latest.items)
      setSelectedComparison(comparison)
      setLatestPhaseArtifact(comparison.phase_artifact)
      setSelectedRun(null)
      setActiveTab('experiments')
      setNotice(`Comparison completed. Best strategy: ${comparison.best_strategy ?? 'n/a'}`)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsRunningExperiment(false)
    }
  }

  function handleSelectedPhaseChange(phaseId: string) {
    setSelectedPhaseId(phaseId)
    const nextConfigId = ragConfigs.find((config) => config.rag_stage === phaseId)?.config_id
    if (nextConfigId) {
      setSelectedConfigId(nextConfigId)
    }
    if (selectedWorkspaceId) {
      getLatestWorkspacePhaseArtifact(selectedWorkspaceId, phaseId)
        .then(setLatestPhaseArtifact)
        .catch(() => setLatestPhaseArtifact(null))
    }
  }

  async function handleSelectExperiment(runId: string) {
    if (!selectedWorkspaceId) {
      return
    }
    setNotice('')
    try {
      const detail = await getWorkspaceExperiment(selectedWorkspaceId, runId)
      setSelectedRun(detail)
      setSelectedComparison(null)
      setSelectedReport(null)
      setActiveTab('experiments')
    } catch (error) {
      setNotice(getErrorMessage(error))
    }
  }

  async function handleViewReport(runId: string) {
    if (!selectedWorkspaceId) {
      return
    }
    setIsLoadingReport(true)
    setNotice('')
    try {
      const report = await getWorkspaceReport(selectedWorkspaceId, runId)
      setSelectedReport(report)
      setActiveTab('reports')
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsLoadingReport(false)
    }
  }

  useEffect(() => {
    let isMounted = true

    refreshHealth()

    listWorkspaces()
      .then((items) => {
        if (!isMounted) {
          return
        }
        setWorkspaces(items)
      })
      .catch((error) => {
        if (isMounted) {
          setNotice(getErrorMessage(error))
        }
      })

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">RAG Experiment Platform for Developers</p>
          <h1>RAG Experiment Platform</h1>
        </div>
        <button className="status-btn" type="button" onClick={refreshHealth}>
          <Activity size={16} />
          <span className={`dot ${health}`} />
          {health === 'checking' ? 'Checking' : health === 'online' ? 'Backend online' : 'Backend offline'}
        </button>
      </header>

      {notice && (
        <div className="notice" role="status">
          <AlertCircle size={16} />
          <span>{notice}</span>
        </div>
      )}

      {!selectedWorkspaceId ? (
        <WorkspaceHome
          workspaceName={workspaceName}
          workspaces={workspaces}
          isCreatingWorkspace={isCreatingWorkspace}
          onWorkspaceNameChange={setWorkspaceName}
          onCreateWorkspace={handleCreateWorkspace}
          onSelectWorkspace={selectWorkspace}
        />
      ) : (
        <section className="workspace-layout">
          <aside className="left-panel">
            <section className="card">
              <div className="card-title">
                <FolderOpen size={17} />
                <h2>{selectedWorkspace?.name ?? 'Workspace'}</h2>
              </div>
              <p className="meta">{selectedWorkspaceId}</p>
              <div className="count-grid">
                <Stat label="Documents" value={String(documents.length)} />
                <Stat label="Golden Qs" value={String(evalQuestions.length)} />
              </div>
              <div className="row-buttons">
                <button className="btn secondary" type="button" onClick={closeWorkspace}>
                  All workspaces
                </button>
                <button
                  className="btn danger"
                  type="button"
                  onClick={handleDeleteWorkspace}
                  disabled={isDeletingWorkspace}
                >
                  {isDeletingWorkspace ? <Loader2 className="spin" size={15} /> : <Trash2 size={15} />}
                  Delete
                </button>
              </div>
            </section>

            <section className="card">
              <div className="card-title">
                <RefreshCcw size={17} />
                <h2>Quick Actions</h2>
              </div>
              <button
                className="btn secondary full"
                type="button"
                onClick={() => selectWorkspace(selectedWorkspaceId)}
              >
                Refresh workspace data
              </button>
              {isLoadingWorkspace && (
                <p className="meta inline">
                  <Loader2 className="spin" size={14} /> Syncing...
                </p>
              )}
            </section>
          </aside>

          <section className="main-panel">
            <nav className="tabs" aria-label="Workspace tabs">
              <TabButton
                isActive={activeTab === 'documents'}
                onClick={() => setActiveTab('documents')}
                icon={<FileText size={15} />}
                label="Documents"
              />
              <TabButton
                isActive={activeTab === 'golden'}
                onClick={() => setActiveTab('golden')}
                icon={<Beaker size={15} />}
                label="Golden Questions"
              />
              <TabButton
                isActive={activeTab === 'experiments'}
                onClick={() => setActiveTab('experiments')}
                icon={<Sparkles size={15} />}
                label="Experiments"
              />
              <TabButton
                isActive={activeTab === 'reports'}
                onClick={() => setActiveTab('reports')}
                icon={<FileText size={15} />}
                label="Reports"
              />
              <TabButton
                isActive={activeTab === 'playground'}
                onClick={() => setActiveTab('playground')}
                icon={<MessageSquare size={15} />}
                label="Playground"
              />
            </nav>

            {activeTab === 'documents' && (
              <DocumentsTab
                documents={documents}
                selectedDocument={selectedDocument}
                selectedDocumentId={selectedDocumentId}
                isLoadingDocument={isLoadingDocument}
                isUploadingDocument={isUploadingDocument}
                onSelectDocument={(documentId) => selectDocument(selectedWorkspaceId, documentId)}
                onUploadDocuments={handleUploadDocuments}
                onUploadDocumentFolder={handleUploadDocumentFolder}
                onDeleteDocument={handleDeleteDocument}
              />
            )}

            {activeTab === 'golden' && (
              <GoldenTab
                evalQuestions={evalQuestions}
                nonStrongLabelCount={weakLabelEvalQuestions.length}
                isUploadingEval={isUploadingEval}
                onUploadEval={handleUploadEval}
                onDeleteEvalQuestion={handleDeleteEvalQuestion}
              />
            )}

            {activeTab === 'experiments' && (
              <ExperimentsTab
                experiments={experiments}
                selectedRun={selectedRun}
                selectedComparison={selectedComparison}
                latestPhaseArtifact={latestPhaseArtifact}
                ragConfigs={ragConfigs}
                selectedConfigId={selectedConfigId}
                ragPhases={ragPhases}
                selectedPhaseId={selectedPhaseId}
                evalQuestionCount={evalQuestions.length}
                nonStrongLabelCount={weakLabelEvalQuestions.length}
                isRunningExperiment={isRunningExperiment}
                onSelectedConfigIdChange={setSelectedConfigId}
                onSelectedPhaseIdChange={handleSelectedPhaseChange}
                onRunExperiment={handleRunExperiment}
                onRunComparison={handleRunComparison}
                onSelectExperiment={handleSelectExperiment}
                onViewReport={handleViewReport}
              />
            )}
            {activeTab === 'reports' && (
              <ReportsTab
                selectedReport={selectedReport}
                isLoadingReport={isLoadingReport}
              />
            )}

            {activeTab === 'playground' && (
              <PlaygroundTab
                question={question}
                answer={answer}
                isQuerying={isQuerying}
                onQuestionChange={setQuestion}
                onQuery={handleQuery}
              />
            )}
          </section>
        </section>
      )}
    </main>
  )
}

function WorkspaceHome({
  workspaceName,
  workspaces,
  isCreatingWorkspace,
  onWorkspaceNameChange,
  onCreateWorkspace,
  onSelectWorkspace,
}: {
  workspaceName: string
  workspaces: WorkspaceSummary[]
  isCreatingWorkspace: boolean
  onWorkspaceNameChange: (value: string) => void
  onCreateWorkspace: () => void
  onSelectWorkspace: (workspaceId: string) => void
}) {
  return (
    <section className="home-grid">
      <section className="card">
        <div className="card-title">
          <Plus size={17} />
          <h2>Create Workspace</h2>
        </div>
        <div className="inline-form">
          <input
            value={workspaceName}
            onChange={(event) => onWorkspaceNameChange(event.target.value)}
            placeholder="Workspace name"
          />
          <button className="btn primary" type="button" onClick={onCreateWorkspace}>
            {isCreatingWorkspace ? <Loader2 className="spin" size={15} /> : <Plus size={15} />}
            Create
          </button>
        </div>
      </section>

      <section className="card">
        <div className="card-title">
          <FolderOpen size={17} />
          <h2>Current Workspaces</h2>
        </div>
        {workspaces.length === 0 ? (
          <p className="meta">No workspaces yet.</p>
        ) : (
          <div className="workspace-grid">
            {workspaces.map((workspace) => (
              <button
                key={workspace.id}
                className="workspace-item"
                type="button"
                onClick={() => onSelectWorkspace(workspace.id)}
              >
                <strong>{workspace.name}</strong>
                <span>{workspace.document_count} documents</span>
              </button>
            ))}
          </div>
        )}
      </section>
    </section>
  )
}

function DocumentsTab({
  documents,
  selectedDocument,
  selectedDocumentId,
  isLoadingDocument,
  isUploadingDocument,
  onSelectDocument,
  onUploadDocuments,
  onUploadDocumentFolder,
  onDeleteDocument,
}: {
  documents: DocumentSummary[]
  selectedDocument: DocumentDetail | null
  selectedDocumentId: string
  isLoadingDocument: boolean
  isUploadingDocument: boolean
  onSelectDocument: (documentId: string) => void
  onUploadDocuments: (files: File[]) => void
  onUploadDocumentFolder: (files: File[]) => void
  onDeleteDocument: (documentId: string) => void
}) {
  return (
    <section className="tab-layout">
      <section className="card">
        <div className="card-title">
          <Upload size={17} />
          <h2>Upload Documents</h2>
        </div>
        <label className="upload">
          <input
            type="file"
            multiple
            accept=".txt,.md"
            onChange={(event) => {
              const selectedFiles = event.target.files ? Array.from(event.target.files) : []
              if (selectedFiles.length > 0) {
                onUploadDocuments(selectedFiles)
                event.target.value = ''
              }
            }}
          />
          {isUploadingDocument ? <Loader2 className="spin" size={16} /> : <Upload size={16} />}
          {isUploadingDocument ? 'Uploading...' : 'Select .txt / .md'}
        </label>
        <label className="upload">
          <input
            type="file"
            multiple
            {...{ webkitdirectory: '' }}
            onChange={(event) => {
              const selectedFiles = event.target.files ? Array.from(event.target.files) : []
              if (selectedFiles.length > 0) {
                onUploadDocumentFolder(selectedFiles)
                event.target.value = ''
              }
            }}
          />
          {isUploadingDocument ? <Loader2 className="spin" size={16} /> : <FolderOpen size={16} />}
          {isUploadingDocument ? 'Uploading corpus...' : 'Select folder'}
        </label>
      </section>

      <section className="card">
        <div className="card-title">
          <FileText size={17} />
          <h2>Documents</h2>
        </div>
        {documents.length === 0 ? (
          <p className="meta">No documents yet.</p>
        ) : (
          <div className="list">
            {documents.map((document) => (
              <button
                className={`list-item ${document.id === selectedDocumentId ? 'active' : ''}`}
                type="button"
                key={document.id}
                onClick={() => onSelectDocument(document.id)}
              >
                <strong>{document.title}</strong>
                <span>
                  {document.file_type.toUpperCase()} | {document.chunk_count} chunks
                </span>
                <span>{document.doc_type} | {document.relative_path || document.file_name}</span>
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="card">
        <div className="card-title">
          <Search size={17} />
          <h2>Document Detail</h2>
        </div>
        {isLoadingDocument ? (
          <p className="meta inline">
            <Loader2 className="spin" size={14} /> Loading document...
          </p>
        ) : selectedDocument ? (
          <>
            <div className="row-between">
              <p className="meta">{selectedDocument.file_name}</p>
              <button className="btn danger" type="button" onClick={() => onDeleteDocument(selectedDocument.id)}>
                <Trash2 size={15} />
                Delete
              </button>
            </div>
            <div className="count-grid">
              <Stat label="Chars" value={String(selectedDocument.content_length)} />
              <Stat label="Chunks" value={String(selectedDocument.chunk_count)} />
              <Stat label="Type" value={selectedDocument.file_type.toUpperCase()} />
              <Stat label="Doc Type" value={selectedDocument.doc_type || 'root'} />
            </div>
            <div className="summary-box">
              <p>
                <strong>Source:</strong> {selectedDocument.source_path || selectedDocument.file_name}
              </p>
              <p>
                <strong>Folder:</strong> {selectedDocument.folder_path || '(root)'}
              </p>
            </div>
            <pre className="preview">{selectedDocument.content}</pre>
          </>
        ) : (
          <p className="meta">Select a document to inspect details.</p>
        )}
      </section>
    </section>
  )
}

function GoldenTab({
  evalQuestions,
  nonStrongLabelCount,
  isUploadingEval,
  onUploadEval,
  onDeleteEvalQuestion,
}: {
  evalQuestions: EvalQuestion[]
  nonStrongLabelCount: number
  isUploadingEval: boolean
  onUploadEval: (file: File) => void
  onDeleteEvalQuestion: (questionId: string) => void
}) {
  return (
    <section className="tab-layout">
      <section className="card">
        <div className="card-title">
          <Upload size={17} />
          <h2>Upload Golden Questions</h2>
        </div>
        <label className="upload">
          <input
            type="file"
            accept=".jsonl,.csv"
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) {
                onUploadEval(file)
                event.target.value = ''
              }
            }}
          />
          {isUploadingEval ? <Loader2 className="spin" size={16} /> : <Upload size={16} />}
          {isUploadingEval ? 'Importing...' : 'Select golden_questions.jsonl or .csv'}
        </label>
      </section>

      <section className="card">
        <div className="card-title">
          <Beaker size={17} />
          <h2>Golden Questions</h2>
        </div>
        {nonStrongLabelCount > 0 && (
          <p className="meta">
            {nonStrongLabelCount} question(s) will use evidence-text or weak-label evaluation instead of direct chunk-id matching.
          </p>
        )}
        {evalQuestions.length === 0 ? (
          <p className="meta">No golden questions yet.</p>
        ) : (
          <div className="qa-list">
            {evalQuestions.map((item) => (
              <article className="qa-item" key={item.id}>
                <div className="row-between">
                  <strong>{item.id}</strong>
                  <button className="icon-danger" type="button" onClick={() => onDeleteEvalQuestion(item.id)}>
                    <Trash2 size={14} />
                  </button>
                </div>
                <p>{item.question}</p>
                <p className="meta">
                  top_k={item.top_k} | label={item.label_type} | expected={item.expected_chunk_ids.join(', ') || '(none)'}
                </p>
                {!!item.category && <p className="meta">category={item.category}</p>}
                {!!item.keywords.length && <p className="meta">keywords={item.keywords.join(', ')}</p>}
              </article>
            ))}
          </div>
        )}
      </section>
    </section>
  )
}

function ExperimentsTab({
  experiments,
  selectedRun,
  selectedComparison,
  latestPhaseArtifact,
  ragConfigs,
  selectedConfigId,
  ragPhases,
  selectedPhaseId,
  evalQuestionCount,
  nonStrongLabelCount,
  isRunningExperiment,
  onSelectedConfigIdChange,
  onSelectedPhaseIdChange,
  onRunExperiment,
  onRunComparison,
  onSelectExperiment,
  onViewReport,
}: {
  experiments: ExperimentSummary[]
  selectedRun: ExperimentRunResponse | null
  selectedComparison: ExperimentComparisonResponse | null
  latestPhaseArtifact: PhaseArtifact | null
  ragConfigs: RagConfigPreset[]
  selectedConfigId: string
  ragPhases: RagPhase[]
  selectedPhaseId: string
  evalQuestionCount: number
  nonStrongLabelCount: number
  isRunningExperiment: boolean
  onSelectedConfigIdChange: (value: string) => void
  onSelectedPhaseIdChange: (value: string) => void
  onRunExperiment: () => void
  onRunComparison: () => void
  onSelectExperiment: (runId: string) => void
  onViewReport: (runId: string) => void
}) {
  const canRunExperiment = evalQuestionCount > 0
  const phaseConfigs = ragConfigs.filter((config) => config.rag_stage === selectedPhaseId)
  const configOptions = phaseConfigs.length > 0 ? phaseConfigs : fallbackRagConfigOptions(selectedPhaseId)
  const selectedConfig = findRagConfig(configOptions, selectedConfigId)
  const phaseOptions = ragPhases.length > 0 ? ragPhases : fallbackRagPhaseOptions()
  const selectedPhase = findRagPhase(phaseOptions, selectedPhaseId)
  const [questionFilter, setQuestionFilter] = useState<QuestionComparisonFilter>('all')
  const [answerReviewFilter, setAnswerReviewFilter] = useState<AnswerReviewFilter>('all')
  const questionComparisons = selectedComparison?.question_comparisons ?? []
  const visibleQuestionComparisons = questionComparisons.filter((row) =>
    matchesQuestionFilter(row, questionFilter),
  )
  const answerReviewResults = selectedRun?.results ?? []
  const visibleAnswerReviewResults = answerReviewResults.filter((item) =>
    matchesAnswerReviewFilter(item, answerReviewFilter),
  )

  return (
    <section className="tab-layout">
      <section className="card">
        <div className="card-title">
          <Sparkles size={17} />
          <h2>Run Evaluation</h2>
        </div>
        {!canRunExperiment && (
          <p className="meta">
            {evalQuestionCount === 0
              ? 'Upload golden questions before running an experiment.'
              : `${nonStrongLabelCount} golden question(s) will use soft labels during evaluation.`}
          </p>
        )}
        {canRunExperiment && nonStrongLabelCount > 0 && (
          <p className="meta">{nonStrongLabelCount} golden question(s) are using evidence-text or weak-label scoring.</p>
        )}
        <div className="inline-form phase-form">
          <select
            value={selectedPhaseId}
            onChange={(event) => onSelectedPhaseIdChange(event.target.value)}
          >
            {phaseOptions.map((phase) => (
              <option value={phase.phase_id} key={phase.phase_id} disabled={!phase.enabled}>
                {phase.name} {phase.enabled ? '' : `(${phase.status})`}
              </option>
            ))}
          </select>
          <span className={`pill ${selectedPhase?.enabled ? 'active_phase' : 'planned_phase'}`}>
            {selectedPhase?.status ?? 'planned'}
          </span>
        </div>
        {selectedPhase && (
          <p className="meta config-note">
            {selectedPhase.phase_id} | {selectedPhase.description}
          </p>
        )}
        <div className="inline-form">
          <select
            value={selectedConfig?.config_id ?? configOptions[0]?.config_id ?? selectedConfigId}
            onChange={(event) => onSelectedConfigIdChange(event.target.value)}
          >
            {configOptions.map((config) => (
              <option value={config.config_id} key={config.config_id}>
                {config.name}
              </option>
            ))}
          </select>
          <button
            className="btn primary"
            type="button"
            onClick={onRunExperiment}
            disabled={isRunningExperiment || !canRunExperiment}
          >
            {isRunningExperiment ? <Loader2 className="spin" size={15} /> : <Beaker size={15} />}
            Run experiment (top_k=5)
          </button>
        </div>
        {selectedConfig && (
          <p className="meta config-note">
            {selectedConfig.config_id} | {formatStageLabel(selectedConfig.rag_stage)} | retriever:{' '}
            {selectedConfig.retriever.type}
          </p>
        )}
        <button
          className="btn secondary full"
          type="button"
          onClick={onRunComparison}
          disabled={isRunningExperiment || !canRunExperiment}
        >
          {isRunningExperiment ? <Loader2 className="spin" size={15} /> : <Activity size={15} />}
          Compare rag_config presets
        </button>
      </section>

      {selectedComparison && (
        <>
          <section className="card">
            <div className="card-title">
              <Activity size={17} />
              <h2>RAG Phase Leaderboard</h2>
            </div>
            <p className="meta">
              {formatStageLabel(selectedComparison.stage)} | top_k={selectedComparison.top_k} |{' '}
              {selectedComparison.created_at}
            </p>
            <div className="count-grid four">
              <Stat label="Tested" value={String(selectedComparison.summary.total_configs)} />
              <Stat label="Candidate Pool" value={String(selectedComparison.summary.candidate_pool_size)} />
              <Stat label="Kept" value={String(selectedComparison.summary.kept_count)} />
              <Stat label="Best" value={selectedComparison.summary.best_config_name ?? 'n/a'} />
            </div>
            <div className="summary-box">
              <p>
                <strong>Fastest:</strong> {selectedComparison.summary.fastest_config_name ?? 'n/a'}
              </p>
              <p>
                <strong>Highest recall:</strong> {selectedComparison.summary.highest_recall_config_name ?? 'n/a'}
              </p>
              <p>{selectedComparison.summary.recommendation}</p>
            </div>
            <div className="table-wrap">
              <table className="leaderboard-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Config</th>
                    <th>Hit@k</th>
                    <th>Recall</th>
                    <th>Precision</th>
                    <th>MRR</th>
                    <th>Chunks</th>
                    <th>Avg Size</th>
                    <th>Coverage</th>
                    <th>Latency</th>
                    <th>Score</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedComparison.leaderboard.map((row) => (
                    <tr key={row.run_id}>
                      <td>{row.rank}</td>
                      <td>
                        <strong>{row.config_name}</strong>
                        <span className="table-subtext">{row.config_id}</span>
                        {row.rag_config && (
                          <span className="table-subtext">{formatRagConfigDetails(row.rag_config)}</span>
                        )}
                        <span className="table-subtext">{row.verdict}</span>
                      </td>
                      <td>{row.metrics.hit_at_k.toFixed(3)}</td>
                      <td>{row.metrics.recall_at_k.toFixed(3)}</td>
                      <td>{row.metrics.precision_at_k.toFixed(3)}</td>
                      <td>{row.metrics.mrr.toFixed(3)}</td>
                      <td>{formatMetricNumber(row.metrics.chunk_count)}</td>
                      <td>{formatMetricNumber(row.metrics.avg_chunk_size)}</td>
                      <td>{formatMetricPercent(row.metrics.coverage_ratio)}</td>
                      <td>{row.metrics.avg_latency_ms.toFixed(1)}ms</td>
                      <td>{row.score.toFixed(3)}</td>
                      <td>
                        <span className={`pill ${row.status}`}>{row.status}</span>
                      </td>
                      <td>
                        <button className="btn secondary" type="button" onClick={() => onSelectExperiment(row.run_id)}>
                          Detail
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="card">
            <div className="card-title">
              <Search size={17} />
              <h2>Question-Level Comparison</h2>
            </div>
            <div className="filter-row">
              <select
                value={questionFilter}
                onChange={(event) => setQuestionFilter(event.target.value as QuestionComparisonFilter)}
              >
                <option value="all">All questions</option>
                <option value="all_failed">All strategies failed</option>
                <option value="partial_hit">Only some strategies hit</option>
                <option value="all_hit">All strategies hit</option>
                <option value="winner_keyword">Keyword wins</option>
                <option value="winner_vector">Vector wins</option>
                <option value="winner_hybrid">Hybrid wins</option>
              </select>
              <span className="meta">
                {visibleQuestionComparisons.length}/{questionComparisons.length} questions
              </span>
            </div>
            {questionComparisons.length === 0 ? (
              <p className="meta">Run a comparison again to generate question-level analysis.</p>
            ) : (
              <div className="table-wrap">
                <table className="question-table">
                  <thead>
                    <tr>
                      <th>Question</th>
                      <th>Expected</th>
                      <th>Keyword</th>
                      <th>Vector</th>
                      <th>Hybrid</th>
                      <th>Winner</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleQuestionComparisons.map((row) => (
                      <tr key={row.question_id}>
                        <td>
                          <strong>{row.question_id}</strong>
                          <span className="table-subtext">{row.question}</span>
                          {row.notes && <span className="table-subtext">notes: {row.notes}</span>}
                        </td>
                        <td>
                          <span className="chunk-list">{formatChunkIds(row.expected_chunk_ids)}</span>
                        </td>
                        <td>
                          <QuestionStrategyCell row={row} strategy="keyword" />
                        </td>
                        <td>
                          <QuestionStrategyCell row={row} strategy="vector" />
                        </td>
                        <td>
                          <QuestionStrategyCell row={row} strategy="hybrid" />
                        </td>
                        <td>{row.winner ? formatStrategyLabel(row.winner) : 'None'}</td>
                        <td>
                          <span className={`pill ${row.status}`}>{formatQuestionStatusLabel(row.status)}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}

      {latestPhaseArtifact && (
        <section className="card">
          <div className="card-title">
            <FileText size={17} />
            <h2>Latest Phase Artifact</h2>
          </div>
          <p className="meta">
            {latestPhaseArtifact.artifact_id} | {formatStageLabel(latestPhaseArtifact.phase_id)} |{' '}
            {latestPhaseArtifact.created_at}
          </p>
          <div className="count-grid four">
            <Stat label="Tested" value={String(latestPhaseArtifact.total_candidates)} />
            <Stat label="Pool Size" value={String(latestPhaseArtifact.candidate_pool_size)} />
            <Stat label="Kept" value={String(latestPhaseArtifact.kept_count)} />
            <Stat label="Best" value={latestPhaseArtifact.best_config_name ?? 'n/a'} />
          </div>
          <div className="summary-box">
            {latestPhaseArtifact.parent_artifact_id && (
              <p>
                <strong>Input artifact:</strong> {latestPhaseArtifact.parent_artifact_id} from{' '}
                {formatStageLabel(latestPhaseArtifact.parent_phase_id ?? 'unknown')}
              </p>
            )}
            <p>
              <strong>Kept config ids:</strong> {formatIdList(latestPhaseArtifact.kept_config_ids)}
            </p>
            <p>
              <strong>Pruned config ids:</strong> {formatIdList(latestPhaseArtifact.pruned_config_ids)}
            </p>
          </div>
          <div className="table-wrap">
            <table className="leaderboard-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Config</th>
                  <th>Hit@k</th>
                  <th>Recall</th>
                  <th>MRR</th>
                  <th>Chunks</th>
                  <th>Coverage</th>
                  <th>Score</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {latestPhaseArtifact.candidates.map((candidate) => (
                  <tr key={`${latestPhaseArtifact.artifact_id}-${candidate.run_id}`}>
                    <td>{candidate.rank}</td>
                    <td>
                      <strong>{candidate.config_name}</strong>
                      <span className="table-subtext">{candidate.config_id}</span>
                      <span className="table-subtext">
                        chunking: {formatChunkingDetails(candidate.chunking_type, candidate.chunking_params)} |
                        retriever: {candidate.retriever_type || candidate.strategy}
                      </span>
                      <span className="table-subtext">{candidate.verdict}</span>
                    </td>
                    <td>{candidate.hit_at_k.toFixed(3)}</td>
                    <td>{candidate.recall_at_k.toFixed(3)}</td>
                    <td>{candidate.mrr.toFixed(3)}</td>
                    <td>{formatMetricNumber(candidate.chunk_count)}</td>
                    <td>{formatMetricPercent(candidate.coverage_ratio)}</td>
                    <td>{candidate.score.toFixed(3)}</td>
                    <td>
                      <span className={`pill ${candidate.status}`}>{candidate.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="card">
        <div className="card-title">
          <FileText size={17} />
          <h2>Experiment Runs</h2>
        </div>
        {experiments.length === 0 ? (
          <p className="meta">No runs yet.</p>
        ) : (
          <div className="qa-list">
            {experiments.map((run) => (
              <article className="qa-item" key={run.run_id}>
                <div className="row-between">
                  <strong>{run.run_id}</strong>
                  <div className="row-buttons">
                    <button className="btn secondary" type="button" onClick={() => onSelectExperiment(run.run_id)}>
                      Detail
                    </button>
                    <button className="btn secondary" type="button" onClick={() => onViewReport(run.run_id)}>
                      Report
                    </button>
                  </div>
                </div>
                <p className="meta">
                  {run.config_name || formatStrategyLabel(run.strategy)} | {run.config_id || run.strategy} | hit@k{' '}
                  {run.metrics.hit_at_k.toFixed(3)} | mrr {run.metrics.mrr.toFixed(3)}
                </p>
              </article>
            ))}
          </div>
        )}
      </section>

      {selectedRun && (
        <>
          <section className="card">
            <div className="card-title">
              <Search size={17} />
              <h2>Run Detail</h2>
            </div>
            <p className="meta">{selectedRun.run_id} | {selectedRun.created_at}</p>
            <p className="meta">
              {selectedRun.config_name || formatStrategyLabel(selectedRun.strategy)} |{' '}
              {selectedRun.config_id || selectedRun.strategy} | {formatStageLabel(selectedRun.rag_stage || 'retriever_evaluation')}
            </p>
            <div className="count-grid">
              <Stat label="Hit@k" value={selectedRun.metrics.hit_at_k.toFixed(3)} />
              <Stat label="Recall@k" value={selectedRun.metrics.recall_at_k.toFixed(3)} />
              <Stat label="Precision@k" value={selectedRun.metrics.precision_at_k.toFixed(3)} />
              <Stat label="MRR" value={selectedRun.metrics.mrr.toFixed(3)} />
            </div>
            {selectedRun.metrics.answer_case_count > 0 && (
              <div className="count-grid">
                <Stat label="Answer Cases" value={String(selectedRun.metrics.answer_case_count)} />
                <Stat label="Ref Cases" value={String(selectedRun.metrics.answer_reference_case_count)} />
                <Stat label="Present Rate" value={selectedRun.metrics.answer_present_rate.toFixed(3)} />
                <Stat label="Answer Match" value={selectedRun.metrics.avg_answer_match_score.toFixed(3)} />
              </div>
            )}
          </section>

          {selectedRun.metrics.answer_case_count > 0 && (
            <section className="card">
              <div className="card-title">
                <MessageSquare size={17} />
                <h2>Answer Review</h2>
              </div>
              <div className="filter-row">
                <select
                  value={answerReviewFilter}
                  onChange={(event) => setAnswerReviewFilter(event.target.value as AnswerReviewFilter)}
                >
                  <option value="all">All answers</option>
                  <option value="with_reference">With reference</option>
                  <option value="low_match">Low match (&lt; 0.20)</option>
                  <option value="high_match">High match (&ge; 0.20)</option>
                </select>
                <span className="meta">
                  {visibleAnswerReviewResults.length}/{answerReviewResults.length} cases
                </span>
              </div>
              <div className="qa-list">
                {visibleAnswerReviewResults.map((result) => (
                  <article className="qa-item" key={`${selectedRun.run_id}-${result.question_id}`}>
                    <div className="row-between">
                      <strong>{result.question_id || result.question}</strong>
                      <span className={`pill ${result.answer_match_score >= 0.2 ? 'hit' : 'miss'}`}>
                        match {result.answer_match_score.toFixed(3)}
                      </span>
                    </div>
                    <p>{result.question}</p>
                    <p className="meta">
                      sources={result.source_count} | hit={String(result.hit)} | recall={result.recall_at_k.toFixed(3)} | precision=
                      {result.precision_at_k.toFixed(3)}
                    </p>
                    <p className="table-subtext">
                      <strong>Generated:</strong> {result.generated_answer || '(none)'}
                    </p>
                    <p className="table-subtext">
                      <strong>Reference:</strong> {result.reference_answer || '(none)'}
                    </p>
                    <p className="table-subtext">
                      <strong>Returned chunks:</strong> {formatChunkIds(result.returned_chunk_ids)}
                    </p>
                  </article>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </section>
  )
}

function ReportsTab({
  selectedReport,
  isLoadingReport,
}: {
  selectedReport: ExperimentReportResponse | null
  isLoadingReport: boolean
}) {
  if (isLoadingReport) {
    return (
      <section className="card">
        <p className="meta inline">
          <Loader2 className="spin" size={14} /> Loading report...
        </p>
      </section>
    )
  }

  if (!selectedReport) {
    return (
      <section className="card">
        <p className="meta">Select "Report" from Experiments tab to view markdown output.</p>
      </section>
    )
  }

  return (
    <section className="card">
      <div className="card-title">
        <FileText size={17} />
        <h2>Report {selectedReport.run_id}</h2>
      </div>
      <pre className="preview">{selectedReport.markdown}</pre>
    </section>
  )
}

function PlaygroundTab({
  question,
  answer,
  isQuerying,
  onQuestionChange,
  onQuery,
}: {
  question: string
  answer: ResearchQueryResponse | null
  isQuerying: boolean
  onQuestionChange: (value: string) => void
  onQuery: () => void
}) {
  return (
    <section className="tab-layout">
      <section className="card">
        <div className="card-title">
          <MessageSquare size={17} />
          <h2>Workspace Playground</h2>
        </div>
        <div className="chat-row">
          <textarea
            value={question}
            onChange={(event) => onQuestionChange(event.target.value)}
            rows={3}
            placeholder="Ask from workspace documents..."
          />
          <button className="btn primary" type="button" onClick={onQuery} disabled={isQuerying}>
            {isQuerying ? <Loader2 className="spin" size={15} /> : <Search size={15} />}
            Ask
          </button>
        </div>
      </section>

      {answer && (
        <section className="card">
          <div className="card-title">
            <Sparkles size={17} />
            <h2>Answer</h2>
          </div>
          <p className="meta">{answer.mode}</p>
          <p>{answer.answer}</p>
          <div className="qa-list">
            {answer.sources.map((source) => (
              <article className="qa-item" key={source.chunk_id}>
                <strong>{source.document_title}</strong>
                <p className="meta">{source.chunk_id} | score {source.score}</p>
                <p>{source.preview}</p>
              </article>
            ))}
          </div>
        </section>
      )}
    </section>
  )
}

function TabButton({
  isActive,
  onClick,
  icon,
  label,
}: {
  isActive: boolean
  onClick: () => void
  icon: ReactNode
  label: string
}) {
  return (
    <button className={`tab-btn ${isActive ? 'active' : ''}`} type="button" onClick={onClick}>
      {icon}
      {label}
    </button>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function findRagConfig(configs: RagConfigPreset[], configId: string): RagConfigPreset | undefined {
  return configs.find((config) => config.config_id === configId)
}

function findRagPhase(phases: RagPhase[], phaseId: string): RagPhase | undefined {
  return phases.find((phase) => phase.phase_id === phaseId)
}

function firstEnabledPhaseId(phases: RagPhase[]) {
  return phases.find((phase) => phase.enabled)?.phase_id ?? DEFAULT_RAG_PHASE_ID
}

function fallbackRagPhaseOptions(): RagPhase[] {
  return [
    buildFallbackRagPhase('baseline_sanity', 'Baseline Sanity', 'planned', false, 0),
    buildFallbackRagPhase('chunking_evaluation', 'Chunking Evaluation', 'active', true, 1),
    buildFallbackRagPhase('retriever_evaluation', 'Retriever Evaluation', 'active', true, 2),
    buildFallbackRagPhase('query_transform_evaluation', 'Query Transform Evaluation', 'active', true, 3),
    buildFallbackRagPhase('reranker_evaluation', 'Reranker Evaluation', 'active', true, 4),
    buildFallbackRagPhase('context_builder_evaluation', 'Context Builder Evaluation', 'active', true, 5),
    buildFallbackRagPhase('answer_evaluation', 'End-to-End Answer Evaluation', 'active', true, 6),
  ]
}

function buildFallbackRagPhase(
  phaseId: string,
  name: string,
  status: string,
  enabled: boolean,
  order: number,
): RagPhase {
  return {
    phase_id: phaseId,
    name,
    description: enabled ? 'Current runnable RAG evaluation phase.' : 'Planned RAG evaluation phase.',
    status,
    enabled,
    order,
  }
}

function strategyFromConfigId(configId: string): RetrievalStrategy {
  if (configId.includes('vector')) {
    return 'vector'
  }
  if (configId.includes('hybrid')) {
    return 'hybrid'
  }
  return 'keyword'
}

function fallbackRagConfigOptions(stage = DEFAULT_RAG_PHASE_ID): RagConfigPreset[] {
  if (stage === 'chunking_evaluation') {
    return [
      buildFallbackRagConfig('cfg_chunk_fixed_500_50', 'Chunk fixed 500 / overlap 50', 'keyword', stage, {
        chunk_size: 500,
        overlap: 50,
      }),
      buildFallbackRagConfig('cfg_chunk_fixed_800_100', 'Chunk fixed 800 / overlap 100', 'keyword', stage, {
        chunk_size: 800,
        overlap: 100,
      }),
      buildFallbackRagConfig('cfg_chunk_fixed_1200_150', 'Chunk fixed 1200 / overlap 150', 'keyword', stage, {
        chunk_size: 1200,
        overlap: 150,
      }),
      buildFallbackRagConfig('cfg_chunk_paragraph_1000', 'Chunk paragraph max 1000', 'keyword', stage, {
        max_chunk_size: 1000,
      }, 'paragraph'),
      buildFallbackRagConfig('cfg_chunk_recursive_500_200', 'Chunk recursive 500 / overlap 200', 'keyword', stage, {
        chunk_size: 500,
        overlap: 200,
      }, 'recursive_character'),
      buildFallbackRagConfig('cfg_chunk_recursive_800_200', 'Chunk recursive 800 / overlap 200', 'keyword', stage, {
        chunk_size: 800,
        overlap: 200,
      }, 'recursive_character'),
      buildFallbackRagConfig('cfg_chunk_recursive_1000_250', 'Chunk recursive 1000 / overlap 250', 'keyword', stage, {
        chunk_size: 1000,
        overlap: 250,
      }, 'recursive_character'),
    ]
  }

  if (stage === 'query_transform_evaluation') {
    return [
      buildFallbackRagConfig('cfg_query_transform_none', 'Query transform none', 'keyword', stage),
      buildFallbackRagConfig('cfg_query_transform_rewrite', 'Query transform simple rewrite', 'keyword', stage),
    ]
  }

  if (stage === 'reranker_evaluation') {
    return [
      buildFallbackRagConfig('cfg_reranker_none', 'Reranker none', 'keyword', stage),
      buildFallbackRagConfig('cfg_reranker_overlap', 'Reranker lexical overlap', 'keyword', stage),
    ]
  }

  if (stage === 'context_builder_evaluation') {
    return [
      buildFallbackRagConfig('cfg_context_plain_top_k', 'Context builder plain top-k', 'keyword', stage),
      buildFallbackRagConfig('cfg_context_document_window', 'Context builder document window', 'keyword', stage),
    ]
  }

  if (stage === 'answer_evaluation') {
    return [
      buildFallbackRagConfig('cfg_answer_grounded_mock', 'Answer grounded mock', 'keyword', stage),
      buildFallbackRagConfig('cfg_answer_extract_then_mock', 'Answer extract then mock', 'keyword', stage),
    ]
  }

  return [
    buildFallbackRagConfig('cfg_keyword_baseline', 'Keyword baseline', 'keyword'),
    buildFallbackRagConfig('cfg_vector_default', 'Vector semantic retrieval', 'vector'),
    buildFallbackRagConfig('cfg_hybrid_default', 'Hybrid keyword + vector', 'hybrid'),
  ]
}

function buildFallbackRagConfig(
  configId: string,
  name: string,
  strategy: RetrievalStrategy,
  stage = DEFAULT_RAG_PHASE_ID,
  chunkingParams: Record<string, number> = { chunk_size: 800, overlap: 100 },
  chunkingType = 'fixed',
): RagConfigPreset {
  const queryTransformType =
    stage === 'query_transform_evaluation' && configId.includes('rewrite') ? 'rewrite' : 'none'
  const rerankerType =
    stage === 'reranker_evaluation' && configId.includes('overlap') ? 'lexical_overlap' : 'none'
  const contextBuilderType =
    stage === 'context_builder_evaluation' && configId.includes('document_window')
      ? 'document_window'
      : 'plain_top_k'
  const answerGeneratorType =
    stage === 'answer_evaluation' && configId.includes('extract_then_mock')
      ? 'extract_then_mock'
      : stage === 'answer_evaluation'
        ? 'grounded_mock'
        : 'none'
  return {
    config_id: configId,
    name,
    description: name,
    rag_stage: stage,
    strategy,
    top_k: 5,
    chunking: { type: chunkingType, params: chunkingParams },
    retriever: { type: strategy, params: { top_k: 5 } },
    query_transform: { type: queryTransformType, params: {} },
    reranker: { type: rerankerType, params: {} },
    context_builder: { type: contextBuilderType, params: {} },
    answer_generator: { type: answerGeneratorType, params: {} },
  }
}

function QuestionStrategyCell({
  row,
  strategy,
}: {
  row: ExperimentQuestionComparisonRow
  strategy: RetrievalStrategy
}) {
  const result = getQuestionStrategyResult(row, strategy)

  if (!result) {
    return <span className="meta">Not run</span>
  }

  return (
    <div className="result-stack">
      <span className={`pill ${result.hit ? 'hit' : 'miss'}`}>{result.hit ? 'hit' : 'miss'}</span>
      <span className="table-subtext">{result.config_name || formatStrategyLabel(result.strategy)}</span>
      <span>
        R {result.recall_at_k.toFixed(3)} | P {result.precision_at_k.toFixed(3)}
      </span>
      <span>
        MRR {result.reciprocal_rank.toFixed(3)} | {result.latency_ms.toFixed(1)}ms
      </span>
      <span className="table-subtext">returned: {formatChunkIds(result.returned_chunk_ids)}</span>
    </div>
  )
}

function getQuestionStrategyResult(
  row: ExperimentQuestionComparisonRow,
  strategy: RetrievalStrategy,
): ExperimentStrategyQuestionResult | undefined {
  const matchingResults = row.strategy_results.filter((item) => item.strategy === strategy)
  return matchingResults.sort(
    (left, right) =>
      Number(right.hit) - Number(left.hit) ||
      right.reciprocal_rank - left.reciprocal_rank ||
      right.recall_at_k - left.recall_at_k ||
      right.precision_at_k - left.precision_at_k ||
      left.latency_ms - right.latency_ms,
  )[0]
}

function matchesQuestionFilter(row: ExperimentQuestionComparisonRow, filter: QuestionComparisonFilter) {
  if (filter === 'all') {
    return true
  }
  if (filter.startsWith('winner_')) {
    return row.winner === filter.replace('winner_', '')
  }
  return row.status === filter
}

function matchesAnswerReviewFilter(result: ExperimentRunResponse['results'][number], filter: AnswerReviewFilter) {
  if (filter === 'all') {
    return true
  }
  if (filter === 'with_reference') {
    return result.reference_answer.trim().length > 0
  }
  if (filter === 'low_match') {
    return result.answer_match_score < 0.2
  }
  if (filter === 'high_match') {
    return result.answer_match_score >= 0.2
  }
  return true
}

function formatQuestionStatusLabel(status: string) {
  const labels: Record<string, string> = {
    all_failed: 'All failed',
    partial_hit: 'Partial hit',
    all_hit: 'All hit',
  }
  return labels[status] ?? status
}

function formatStrategyLabel(strategy: string) {
  const labels: Record<string, string> = {
    keyword: 'Keyword',
    vector: 'Vector',
    hybrid: 'Hybrid',
  }
  return labels[strategy] ?? strategy
}

function formatChunkIds(chunkIds: string[]) {
  return chunkIds.length > 0 ? chunkIds.join(', ') : '(none)'
}

function formatIdList(ids: string[]) {
  return ids.length > 0 ? ids.join(', ') : '(none)'
}

function formatMetricNumber(value: number) {
  return value > 0 ? value.toFixed(0) : 'n/a'
}

function formatMetricPercent(value: number) {
  return value > 0 ? value.toFixed(3) : 'n/a'
}

function formatRagConfigDetails(config: RagConfigPreset) {
  const queryTransform =
    config.query_transform.type && config.query_transform.type !== 'none'
      ? ` | query transform: ${config.query_transform.type}`
      : ''
  const reranker =
    config.reranker.type && config.reranker.type !== 'none' ? ` | reranker: ${config.reranker.type}` : ''
  const contextBuilder =
    config.context_builder.type && config.context_builder.type !== 'plain_top_k'
      ? ` | context builder: ${config.context_builder.type}`
      : ''
  const answerGenerator =
    config.answer_generator.type && config.answer_generator.type !== 'none'
      ? ` | answer: ${config.answer_generator.type}`
      : ''
  return `chunking: ${formatChunkingDetails(config.chunking.type, config.chunking.params)} | retriever: ${
    config.retriever.type
  }${queryTransform}${reranker}${contextBuilder}${answerGenerator}`
}

function formatChunkingDetails(
  chunkingType: string,
  params: Record<string, string | number | boolean>,
) {
  const paramText = Object.entries(params)
    .map(([key, value]) => `${key}=${value}`)
    .join(', ')
  return paramText ? `${chunkingType} (${paramText})` : chunkingType
}

function formatStageLabel(stage: string) {
  return stage
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message
  }
  return 'Something went wrong'
}

function isSupportedDocumentFile(file: File) {
  const fileName = file.name.toLowerCase()
  return fileName.endsWith('.txt') || fileName.endsWith('.md')
}

export default App
