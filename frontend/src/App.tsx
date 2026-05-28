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
  createWorkspace,
  deleteWorkspace,
  deleteWorkspaceDocument,
  deleteWorkspaceEvalQuestion,
  fetchHealth,
  fetchWorkspaceDocument,
  listWorkspaceDocuments,
  listWorkspaceEvalQuestions,
  listWorkspaces,
  queryWorkspaceResearch,
  uploadWorkspaceDocument,
  uploadWorkspaceEvalQuestions,
} from './api/client'
import type {
  DocumentDetail,
  DocumentSummary,
  EvalQuestion,
  ResearchQueryResponse,
  WorkspaceSummary,
} from './types/api'

type HealthState = 'checking' | 'online' | 'offline'
type WorkspaceTab = 'documents' | 'golden' | 'experiments' | 'reports' | 'playground'

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
  const [question, setQuestion] = useState('What does this workspace say about FastAPI?')
  const [answer, setAnswer] = useState<ResearchQueryResponse | null>(null)

  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false)
  const [isDeletingWorkspace, setIsDeletingWorkspace] = useState(false)
  const [isLoadingWorkspace, setIsLoadingWorkspace] = useState(false)
  const [isUploadingDocument, setIsUploadingDocument] = useState(false)
  const [isUploadingEval, setIsUploadingEval] = useState(false)
  const [isLoadingDocument, setIsLoadingDocument] = useState(false)
  const [isQuerying, setIsQuerying] = useState(false)

  const selectedWorkspace = useMemo(
    () => workspaces.find((workspace) => workspace.id === selectedWorkspaceId),
    [workspaces, selectedWorkspaceId],
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
      setSelectedDocumentId('')
      setSelectedDocument(null)
      return
    }

    setIsLoadingWorkspace(true)
    try {
      const [workspaceDocuments, workspaceEval] = await Promise.all([
        listWorkspaceDocuments(workspaceId),
        listWorkspaceEvalQuestions(workspaceId),
      ])
      setDocuments(workspaceDocuments)
      setEvalQuestions(workspaceEval.items)
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

  async function handleUploadDocument(file: File) {
    if (!selectedWorkspaceId) {
      return
    }

    setIsUploadingDocument(true)
    setNotice('')
    try {
      const uploaded = await uploadWorkspaceDocument(selectedWorkspaceId, file)
      const workspaceDocuments = await listWorkspaceDocuments(selectedWorkspaceId)
      setDocuments(workspaceDocuments)
      setSelectedDocumentId(uploaded.id)
      setSelectedDocument(uploaded)
      await refreshWorkspaces(selectedWorkspaceId)
      setNotice(`Uploaded ${uploaded.file_name}`)
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
        top_k: 3,
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
    setSelectedDocumentId('')
    setSelectedDocument(null)
    setAnswer(null)
    setActiveTab('documents')
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
          <p className="eyebrow">Agentic Research OS</p>
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
                onUploadDocument={handleUploadDocument}
                onDeleteDocument={handleDeleteDocument}
              />
            )}

            {activeTab === 'golden' && (
              <GoldenTab
                evalQuestions={evalQuestions}
                isUploadingEval={isUploadingEval}
                onUploadEval={handleUploadEval}
                onDeleteEvalQuestion={handleDeleteEvalQuestion}
              />
            )}

            {activeTab === 'experiments' && <ComingSoon title="Experiments" />}
            {activeTab === 'reports' && <ComingSoon title="Reports" />}

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
  onUploadDocument,
  onDeleteDocument,
}: {
  documents: DocumentSummary[]
  selectedDocument: DocumentDetail | null
  selectedDocumentId: string
  isLoadingDocument: boolean
  isUploadingDocument: boolean
  onSelectDocument: (documentId: string) => void
  onUploadDocument: (file: File) => void
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
            accept=".txt,.md"
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) {
                onUploadDocument(file)
                event.target.value = ''
              }
            }}
          />
          {isUploadingDocument ? <Loader2 className="spin" size={16} /> : <Upload size={16} />}
          {isUploadingDocument ? 'Uploading...' : 'Select .txt / .md'}
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
  isUploadingEval,
  onUploadEval,
  onDeleteEvalQuestion,
}: {
  evalQuestions: EvalQuestion[]
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
            accept=".jsonl"
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) {
                onUploadEval(file)
                event.target.value = ''
              }
            }}
          />
          {isUploadingEval ? <Loader2 className="spin" size={16} /> : <Upload size={16} />}
          {isUploadingEval ? 'Importing...' : 'Select golden_questions.jsonl'}
        </label>
      </section>

      <section className="card">
        <div className="card-title">
          <Beaker size={17} />
          <h2>Golden Questions</h2>
        </div>
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
                <p className="meta">top_k={item.top_k} | expected={item.expected_chunk_ids.join(', ') || '(none)'}</p>
              </article>
            ))}
          </div>
        )}
      </section>
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

function ComingSoon({ title }: { title: string }) {
  return (
    <section className="card">
      <div className="card-title">
        <Sparkles size={17} />
        <h2>{title}</h2>
      </div>
      <p className="meta">This tab is reserved for next phase implementation.</p>
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

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message
  }
  return 'Something went wrong'
}

export default App
