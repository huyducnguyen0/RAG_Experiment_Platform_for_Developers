import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertCircle,
  Database,
  FileText,
  Folder,
  Loader2,
  Plus,
  RefreshCcw,
  Save,
  Search,
  Sparkles,
  Trash2,
  Upload,
} from 'lucide-react'
import {
  createWorkspace,
  deleteWorkspaceDocument,
  fetchHealth,
  fetchWorkspaceDocument,
  listWorkspaceDocuments,
  listWorkspaces,
  queryWorkspaceResearch,
  renameWorkspace,
  uploadWorkspaceDocument,
} from './api/client'
import type {
  DocumentDetail,
  DocumentSummary,
  ResearchQueryResponse,
  WorkspaceSummary,
} from './types/api'

type HealthState = 'checking' | 'online' | 'offline'

function App() {
  const [health, setHealth] = useState<HealthState>('checking')
  const [workspaces, setWorkspaces] = useState<WorkspaceSummary[]>([])
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState('')
  const [workspaceName, setWorkspaceName] = useState('New research workspace')
  const [selectedWorkspaceName, setSelectedWorkspaceName] = useState('')
  const [documents, setDocuments] = useState<DocumentSummary[]>([])
  const [selectedDocumentId, setSelectedDocumentId] = useState('')
  const [selectedDocument, setSelectedDocument] = useState<DocumentDetail | null>(null)
  const [question, setQuestion] = useState('What does this workspace say about RAG?')
  const [answer, setAnswer] = useState<ResearchQueryResponse | null>(null)
  const [summary, setSummary] = useState<ResearchQueryResponse | null>(null)
  const [notice, setNotice] = useState('')
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false)
  const [isRenamingWorkspace, setIsRenamingWorkspace] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isLoadingDocument, setIsLoadingDocument] = useState(false)
  const [isQuerying, setIsQuerying] = useState(false)
  const [isSummarizing, setIsSummarizing] = useState(false)

  const selectedWorkspace = useMemo(
    () => workspaces.find((workspace) => workspace.id === selectedWorkspaceId),
    [workspaces, selectedWorkspaceId],
  )

  const selectedDocumentSummary = useMemo(
    () => documents.find((document) => document.id === selectedDocumentId),
    [documents, selectedDocumentId],
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
      await selectWorkspace(nextWorkspaceId)
      return
    }

    if (!selectedWorkspaceId && items.length > 0) {
      await selectWorkspace(items[0].id)
      return
    }

    if (selectedWorkspaceId && !items.some((item) => item.id === selectedWorkspaceId)) {
      await selectWorkspace(items[0]?.id ?? '')
    }
  }

  async function selectWorkspace(workspaceId: string) {
    setSelectedWorkspaceId(workspaceId)
    setSelectedDocumentId('')
    setSelectedDocument(null)
    setAnswer(null)
    setSummary(null)

    if (!workspaceId) {
      setDocuments([])
      setSelectedWorkspaceName('')
      return
    }

    const workspace = workspaces.find((item) => item.id === workspaceId)
    setSelectedWorkspaceName(workspace?.name ?? '')

    const workspaceDocuments = await listWorkspaceDocuments(workspaceId)
    setDocuments(workspaceDocuments)

    if (workspaceDocuments.length > 0) {
      await selectDocument(workspaceId, workspaceDocuments[0].id)
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
      const workspace = await createWorkspace(workspaceName)
      setWorkspaceName('New research workspace')
      setSelectedWorkspaceName(workspace.name)
      await refreshWorkspaces(workspace.id)
      setNotice(`Created workspace ${workspace.name}`)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsCreatingWorkspace(false)
    }
  }

  async function handleRenameWorkspace() {
    if (!selectedWorkspaceId) {
      setNotice('Select a workspace first')
      return
    }

    setIsRenamingWorkspace(true)
    setNotice('')

    try {
      const renamed = await renameWorkspace(selectedWorkspaceId, selectedWorkspaceName)
      setWorkspaces((items) =>
        items.map((item) =>
          item.id === renamed.id
            ? { ...item, name: renamed.name }
            : item,
        ),
      )
      setSelectedWorkspaceName(renamed.name)
      setNotice(`Renamed workspace to ${renamed.name}`)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsRenamingWorkspace(false)
    }
  }

  async function handleUpload(file: File) {
    if (!selectedWorkspaceId) {
      setNotice('Create or select a workspace first')
      return
    }

    setIsUploading(true)
    setNotice('')
    try {
      const uploaded = await uploadWorkspaceDocument(selectedWorkspaceId, file)
      const workspaceDocuments = await listWorkspaceDocuments(selectedWorkspaceId)
      setDocuments(workspaceDocuments)
      setSelectedDocumentId(uploaded.id)
      setSelectedDocument(uploaded)
      setNotice(`Uploaded ${uploaded.file_name}`)
      await refreshWorkspaces(selectedWorkspaceId)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsUploading(false)
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
      setSelectedDocumentId('')
      setSelectedDocument(null)
      if (workspaceDocuments.length > 0) {
        await selectDocument(selectedWorkspaceId, workspaceDocuments[0].id)
      }
      await refreshWorkspaces(selectedWorkspaceId)
      setNotice('Document deleted')
    } catch (error) {
      setNotice(getErrorMessage(error))
    }
  }

  async function handleResearchQuery() {
    if (!selectedWorkspaceId) {
      setNotice('Create or select a workspace first')
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

  async function handleSummarizeWorkspace() {
    if (!selectedWorkspaceId) {
      setNotice('Create or select a workspace first')
      return
    }

    setIsSummarizing(true)
    setNotice('')
    try {
      const result = await queryWorkspaceResearch(selectedWorkspaceId, {
        question: 'Summarize the key points in this workspace.',
        top_k: 5,
      })
      setSummary(result)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsSummarizing(false)
    }
  }

  function closeWorkspace() {
    setSelectedWorkspaceId('')
    setSelectedWorkspaceName('')
    setSelectedDocumentId('')
    setSelectedDocument(null)
    setDocuments([])
    setAnswer(null)
    setSummary(null)
  }

  useEffect(() => {
    let isMounted = true

    fetchHealth()
      .then(() => {
        if (isMounted) {
          setHealth('online')
        }
      })
      .catch(() => {
        if (isMounted) {
          setHealth('offline')
        }
      })

    listWorkspaces()
      .then(async (items) => {
        if (!isMounted) {
          return
        }

        if (items.length === 0) {
          const workspace = await createWorkspace('My Research Workspace')
          if (!isMounted) {
            return
          }
          setWorkspaces([workspace])
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
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Agentic Research OS</p>
          <h1>Notebook Workspace</h1>
        </div>
        <button className="status-button" type="button" onClick={refreshHealth}>
          <Activity size={18} aria-hidden="true" />
          <span className={`status-dot ${health}`}></span>
          {health === 'checking' ? 'Checking' : health === 'online' ? 'Backend online' : 'Backend offline'}
        </button>
      </header>

      {notice && (
        <div className="notice" role="status">
          <AlertCircle size={18} aria-hidden="true" />
          <span>{notice}</span>
        </div>
      )}

      {!selectedWorkspaceId ? (
        <WorkspaceLobby
          workspaceName={workspaceName}
          workspaces={workspaces}
          isCreatingWorkspace={isCreatingWorkspace}
          onWorkspaceNameChange={setWorkspaceName}
          onCreateWorkspace={handleCreateWorkspace}
          onSelectWorkspace={selectWorkspace}
        />
      ) : (
        <section className="workspace">
          <aside className="sidebar" aria-label="Workspace and document controls">
          <section className="panel workspace-panel">
            <div className="panel-heading with-action">
              <div>
                <Folder size={18} aria-hidden="true" />
                <h2>{selectedWorkspace?.name ?? 'Workspace'}</h2>
              </div>
              <button className="secondary-button" type="button" onClick={closeWorkspace}>
                All workspaces
              </button>
            </div>
            <div className="rename-row compact">
              <input
                value={selectedWorkspaceName}
                onChange={(event) => setSelectedWorkspaceName(event.target.value)}
                placeholder="Selected workspace name"
              />
              <button
                className="icon-button"
                type="button"
                onClick={handleRenameWorkspace}
                title="Rename selected workspace"
                disabled={isRenamingWorkspace}
              >
                {isRenamingWorkspace ? (
                  <Loader2 className="spin" size={17} aria-hidden="true" />
                ) : (
                  <Save size={17} aria-hidden="true" />
                )}
              </button>
            </div>
          </section>

          <section className="panel upload-panel">
            <div className="panel-heading">
              <Upload size={18} aria-hidden="true" />
              <h2>Upload to Workspace</h2>
            </div>
            <label className="upload-zone">
              <input
                type="file"
                accept=".txt,.md"
                onChange={(event) => {
                  const file = event.target.files?.[0]
                  if (file) {
                    handleUpload(file)
                    event.target.value = ''
                  }
                }}
              />
              {isUploading ? (
                <Loader2 className="spin" size={22} aria-hidden="true" />
              ) : (
                <FileText size={22} aria-hidden="true" />
              )}
              <span>{isUploading ? 'Uploading...' : 'Choose .txt or .md'}</span>
            </label>
          </section>

          <section className="panel document-panel">
            <div className="panel-heading with-action">
              <div>
                <Database size={18} aria-hidden="true" />
                <h2>Documents</h2>
              </div>
              <button
                className="icon-button"
                type="button"
                onClick={() => selectedWorkspaceId && selectWorkspace(selectedWorkspaceId)}
                title="Refresh documents"
              >
                <RefreshCcw size={17} aria-hidden="true" />
              </button>
            </div>
            <div className="document-list">
              {documents.length === 0 ? (
                <p className="muted">No documents in this workspace yet.</p>
              ) : (
                documents.map((document) => (
                  <button
                    key={document.id}
                    className={`document-item ${document.id === selectedDocumentId ? 'active' : ''}`}
                    type="button"
                    onClick={() => selectDocument(selectedWorkspaceId, document.id)}
                  >
                    <span className="document-title">{document.title}</span>
                    <span className="document-meta">
                      {document.file_type.toUpperCase()} | {document.chunk_count} chunks | {document.content_length} chars
                    </span>
                  </button>
                ))
              )}
            </div>
          </section>
        </aside>

        <section className="content-area">
          <section className="panel detail-panel">
            <div className="panel-heading with-action">
              <div>
                <FileText size={18} aria-hidden="true" />
                <h2>{selectedDocumentSummary?.title ?? selectedWorkspace?.name ?? 'Workspace Detail'}</h2>
              </div>
              {selectedDocument && (
                <button
                  className="danger-button"
                  type="button"
                  onClick={() => handleDeleteDocument(selectedDocument.id)}
                >
                  <Trash2 size={16} aria-hidden="true" />
                  Delete
                </button>
              )}
            </div>

            {isLoadingDocument ? (
              <div className="loading-line">
                <Loader2 className="spin" size={18} aria-hidden="true" />
                Loading document
              </div>
            ) : selectedDocument ? (
              <DocumentDetailView document={selectedDocument} />
            ) : (
              <p className="muted">Upload a document to the selected workspace to inspect content and chunks.</p>
            )}
          </section>

          <section className="panel research-panel">
            <div className="panel-heading with-action">
              <div>
                <Search size={18} aria-hidden="true" />
                <h2>Workspace Chat</h2>
              </div>
              <button
                className="secondary-button"
                type="button"
                onClick={handleSummarizeWorkspace}
                disabled={isSummarizing}
              >
                {isSummarizing ? (
                  <Loader2 className="spin" size={16} aria-hidden="true" />
                ) : (
                  <Sparkles size={16} aria-hidden="true" />
                )}
                Summarize
              </button>
            </div>
            <div className="query-row">
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                rows={3}
                placeholder="Ask about documents in the selected workspace"
              />
              <button className="primary-button" type="button" onClick={handleResearchQuery} disabled={isQuerying}>
                {isQuerying ? <Loader2 className="spin" size={17} aria-hidden="true" /> : <Search size={17} aria-hidden="true" />}
                Ask
              </button>
            </div>

            {answer && (
              <div className="answer-layout">
                <section className="answer-box">
                  <div className="answer-meta">{answer.mode}</div>
                  <p>{answer.answer}</p>
                </section>
                <SourceList answer={answer} />
              </div>
            )}
            {summary && (
              <div className="answer-layout summary-layout">
                <section className="answer-box">
                  <div className="answer-meta">workspace summary</div>
                  <p>{summary.answer}</p>
                </section>
                <SourceList answer={summary} />
              </div>
            )}
          </section>
        </section>
      </section>
      )}
    </main>
  )
}

function WorkspaceLobby({
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
    <section className="workspace-lobby">
      <section className="panel lobby-create-panel">
        <div className="panel-heading">
          <Plus size={18} aria-hidden="true" />
          <h2>Create Workspace</h2>
        </div>
        <div className="create-row large">
          <input
            value={workspaceName}
            onChange={(event) => onWorkspaceNameChange(event.target.value)}
            placeholder="Workspace name"
          />
          <button className="primary-button" type="button" onClick={onCreateWorkspace}>
            {isCreatingWorkspace ? (
              <Loader2 className="spin" size={17} aria-hidden="true" />
            ) : (
              <Plus size={17} aria-hidden="true" />
            )}
            Create
          </button>
        </div>
      </section>

      <section className="panel lobby-list-panel">
        <div className="panel-heading">
          <Folder size={18} aria-hidden="true" />
          <h2>Current Workspaces</h2>
        </div>
        {workspaces.length === 0 ? (
          <p className="muted">No workspaces yet.</p>
        ) : (
          <div className="workspace-grid">
            {workspaces.map((workspace) => (
              <button
                key={workspace.id}
                className="workspace-card"
                type="button"
                onClick={() => onSelectWorkspace(workspace.id)}
              >
                <span>{workspace.name}</span>
                <small>{workspace.document_count} documents</small>
              </button>
            ))}
          </div>
        )}
      </section>
    </section>
  )
}

function DocumentDetailView({ document }: { document: DocumentDetail }) {
  return (
    <div className="document-detail">
      <div className="stats-grid">
        <Stat label="Type" value={document.file_type.toUpperCase()} />
        <Stat label="Characters" value={String(document.content_length)} />
        <Stat label="Chunks" value={String(document.chunk_count)} />
      </div>
      <pre className="content-preview">{document.content}</pre>
      <div className="chunk-list">
        {document.chunks.map((chunk) => (
          <article className="chunk-item" key={chunk.chunk_id}>
            <div className="chunk-header">
              <span>{chunk.chunk_id}</span>
              <span>{chunk.start_index}-{chunk.end_index}</span>
            </div>
            <p>{chunk.content}</p>
          </article>
        ))}
      </div>
    </div>
  )
}

function SourceList({ answer }: { answer: ResearchQueryResponse }) {
  if (answer.sources.length === 0) {
    return <p className="muted">No sources returned from this workspace.</p>
  }

  return (
    <section className="source-list" aria-label="Research sources">
      {answer.sources.map((source) => (
        <article className="source-item" key={source.chunk_id}>
          <div className="source-header">
            <span>{source.document_title}</span>
            <strong>score {source.score}</strong>
          </div>
          <code>{source.chunk_id}</code>
          <p>{source.preview}</p>
        </article>
      ))}
    </section>
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
