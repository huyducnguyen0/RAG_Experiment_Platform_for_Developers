import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertCircle,
  Database,
  FileText,
  Loader2,
  RefreshCcw,
  Search,
  Trash2,
  Upload,
} from 'lucide-react'
import {
  deleteDocument,
  fetchDocument,
  fetchHealth,
  listDocuments,
  queryResearch,
  uploadDocument,
} from './api/client'
import type {
  DocumentDetail,
  DocumentSummary,
  ResearchQueryResponse,
} from './types/api'

type HealthState = 'checking' | 'online' | 'offline'

function App() {
  const [health, setHealth] = useState<HealthState>('checking')
  const [documents, setDocuments] = useState<DocumentSummary[]>([])
  const [selectedId, setSelectedId] = useState<string>('')
  const [selectedDocument, setSelectedDocument] = useState<DocumentDetail | null>(null)
  const [question, setQuestion] = useState('What does this document say about RAG?')
  const [answer, setAnswer] = useState<ResearchQueryResponse | null>(null)
  const [notice, setNotice] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [isLoadingDocument, setIsLoadingDocument] = useState(false)
  const [isQuerying, setIsQuerying] = useState(false)

  const selectedDocumentSummary = useMemo(
    () => documents.find((document) => document.id === selectedId),
    [documents, selectedId],
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

  async function refreshDocuments(nextSelectedId?: string) {
    const items = await listDocuments()
    setDocuments(items)

    if (nextSelectedId) {
      await selectDocument(nextSelectedId)
      return
    }

    if (!selectedId && items.length > 0) {
      await selectDocument(items[0].id)
      return
    }

    if (selectedId && !items.some((item) => item.id === selectedId)) {
      await selectDocument(items[0]?.id ?? '')
    }
  }

  async function loadDocument(documentId: string) {
    if (!documentId) {
      setSelectedDocument(null)
      return
    }

    setIsLoadingDocument(true)
    try {
      const detail = await fetchDocument(documentId)
      setSelectedDocument(detail)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsLoadingDocument(false)
    }
  }

  async function selectDocument(documentId: string) {
    setSelectedId(documentId)
    await loadDocument(documentId)
  }

  async function handleUpload(file: File) {
    setIsUploading(true)
    setNotice('')
    try {
      const uploaded = await uploadDocument(file)
      await refreshDocuments(uploaded.id)
      setSelectedDocument(uploaded)
      setNotice(`Uploaded ${uploaded.file_name}`)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsUploading(false)
    }
  }

  async function handleDelete(documentId: string) {
    setNotice('')
    try {
      await deleteDocument(documentId)
      if (selectedId === documentId) {
        setSelectedId('')
        setSelectedDocument(null)
      }
      await refreshDocuments()
      setNotice('Document deleted')
    } catch (error) {
      setNotice(getErrorMessage(error))
    }
  }

  async function handleResearchQuery() {
    setIsQuerying(true)
    setNotice('')
    try {
      const result = await queryResearch({ question, top_k: 3 })
      setAnswer(result)
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setIsQuerying(false)
    }
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

    listDocuments()
      .then((items) => {
        if (!isMounted) {
          return null
        }

        setDocuments(items)
        const firstDocumentId = items[0]?.id

        if (!firstDocumentId) {
          return null
        }

        setSelectedId(firstDocumentId)
        return fetchDocument(firstDocumentId)
      })
      .then((detail) => {
        if (isMounted && detail) {
          setSelectedDocument(detail)
        }
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
          <h1>Research Workspace</h1>
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

      <section className="workspace">
        <aside className="sidebar" aria-label="Document controls">
          <section className="panel upload-panel">
            <div className="panel-heading">
              <Upload size={18} aria-hidden="true" />
              <h2>Upload</h2>
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
              <button className="icon-button" type="button" onClick={() => refreshDocuments()} title="Refresh documents">
                <RefreshCcw size={17} aria-hidden="true" />
              </button>
            </div>
            <div className="document-list">
              {documents.length === 0 ? (
                <p className="muted">No documents yet.</p>
              ) : (
                documents.map((document) => (
                  <button
                    key={document.id}
                    className={`document-item ${document.id === selectedId ? 'active' : ''}`}
                    type="button"
                    onClick={() => selectDocument(document.id)}
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
                <h2>{selectedDocumentSummary?.title ?? 'Document Detail'}</h2>
              </div>
              {selectedDocument && (
                <button
                  className="danger-button"
                  type="button"
                  onClick={() => handleDelete(selectedDocument.id)}
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
              <p className="muted">Select or upload a document to inspect its content and chunks.</p>
            )}
          </section>

          <section className="panel research-panel">
            <div className="panel-heading">
              <Search size={18} aria-hidden="true" />
              <h2>Research Query</h2>
            </div>
            <div className="query-row">
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                rows={3}
                placeholder="Ask a question about your uploaded documents"
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
          </section>
        </section>
      </section>
    </main>
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
    return <p className="muted">No sources returned.</p>
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
