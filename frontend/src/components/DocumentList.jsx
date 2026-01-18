import { useState, useEffect } from 'react'
import './DocumentList.css'

function DocumentList({ refreshTrigger }) {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(null)

  const fetchDocuments = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8001/api/documents')

      if (!response.ok) {
        throw new Error('Failed to fetch documents')
      }

      const data = await response.json()
      setDocuments(data.documents || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [refreshTrigger])

  const handleDelete = async (docId, filename) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
      return
    }

    setDeleting(docId)

    try {
      const response = await fetch(`http://localhost:8001/api/documents/${docId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error('Failed to delete document')
      }

      // Refresh the document list
      await fetchDocuments()
    } catch (err) {
      alert(`Failed to delete document: ${err.message}`)
    } finally {
      setDeleting(null)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const getFileTypeIcon = (fileType) => {
    const icons = {
      '.pdf': '📄',
      '.docx': '📝',
      '.txt': '📃',
      '.md': '📋'
    }
    return icons[fileType] || '📁'
  }

  if (loading) {
    return (
      <div className="document-list">
        <h3>Uploaded Documents</h3>
        <div className="loading">Loading documents...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="document-list">
        <h3>Uploaded Documents</h3>
        <div className="error-message">{error}</div>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="document-list">
        <h3>Uploaded Documents</h3>
        <div className="empty-state">
          <p>No documents uploaded yet</p>
          <p className="empty-hint">Upload a ZIP file to get started</p>
        </div>
      </div>
    )
  }

  return (
    <div className="document-list">
      <h3>Uploaded Documents ({documents.length})</h3>
      <div className="documents-grid">
        {documents.map((doc) => (
          <div key={doc.id} className="document-card">
            <div className="document-icon">
              {getFileTypeIcon(doc.file_type)}
            </div>
            <div className="document-info">
              <div className="document-name" title={doc.filename}>
                {doc.filename}
              </div>
              <div className="document-meta">
                <span className="file-size">{formatFileSize(doc.file_size)}</span>
                <span className="file-type">{doc.file_type}</span>
                <span className={`status status-${doc.status}`}>{doc.status}</span>
              </div>
              <div className="document-date">{formatDate(doc.uploaded_at)}</div>
            </div>
            <button
              className="delete-button"
              onClick={() => handleDelete(doc.id, doc.filename)}
              disabled={deleting === doc.id}
              title="Delete document"
            >
              {deleting === doc.id ? '⏳' : '🗑️'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default DocumentList
