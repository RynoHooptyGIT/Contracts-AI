import { useState, useEffect } from 'react'
import './DocumentList.css'
import TemplateManager from './TemplateManager'

function DocumentList({ refreshTrigger }) {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [templates, setTemplates] = useState([])
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState(null)
  const [templateCategory, setTemplateCategory] = useState('')
  const [templateNotes, setTemplateNotes] = useState('')
  const [creatingTemplate, setCreatingTemplate] = useState(false)
  const [showTemplateManager, setShowTemplateManager] = useState(false)

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

  const fetchTemplates = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/templates')
      if (response.ok) {
        const data = await response.json()
        setTemplates(data.templates || [])
      }
    } catch (err) {
      console.error('Failed to fetch templates:', err)
    }
  }

  useEffect(() => {
    fetchDocuments()
    fetchTemplates()
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

  const isDocumentTemplate = (docId) => {
    return templates.find(t => t.document_id === docId)
  }

  const handleMarkAsTemplate = (doc) => {
    setSelectedDocument(doc)
    setTemplateCategory('')
    setTemplateNotes('')
    setShowTemplateModal(true)
  }

  const handleCloseModal = () => {
    setShowTemplateModal(false)
    setSelectedDocument(null)
    setTemplateCategory('')
    setTemplateNotes('')
  }

  const handleCreateTemplate = async (e) => {
    e.preventDefault()

    if (!templateCategory) {
      alert('Please select a category')
      return
    }

    setCreatingTemplate(true)

    try {
      const response = await fetch('http://localhost:8001/api/templates/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_id: selectedDocument.id,
          category: templateCategory,
          notes: templateNotes || undefined
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create template')
      }

      // Refresh templates list
      await fetchTemplates()
      handleCloseModal()
      alert('Template created successfully!')
    } catch (err) {
      alert(`Failed to create template: ${err.message}`)
    } finally {
      setCreatingTemplate(false)
    }
  }

  const getTemplateStatusBadge = (template) => {
    const statusColors = {
      pending: '#fbbf24',
      approved: '#4ade80',
      inactive: '#888'
    }
    return {
      text: template.status,
      color: statusColors[template.status] || '#888'
    }
  }

  if (showTemplateManager) {
    return (
      <div className="document-list">
        <div className="document-list-header">
          <h3>Template Manager</h3>
          <button
            className="template-manager-toggle"
            onClick={() => setShowTemplateManager(false)}
          >
            Back to Documents
          </button>
        </div>
        <TemplateManager />
      </div>
    )
  }

  if (loading) {
    return (
      <div className="document-list">
        <div className="document-list-header">
          <h3>Uploaded Documents</h3>
          <button
            className="template-manager-toggle"
            onClick={() => setShowTemplateManager(true)}
          >
            Manage Templates
          </button>
        </div>
        <div className="loading">Loading documents...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="document-list">
        <div className="document-list-header">
          <h3>Uploaded Documents</h3>
          <button
            className="template-manager-toggle"
            onClick={() => setShowTemplateManager(true)}
          >
            Manage Templates
          </button>
        </div>
        <div className="error-message">{error}</div>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="document-list">
        <div className="document-list-header">
          <h3>Uploaded Documents</h3>
          <button
            className="template-manager-toggle"
            onClick={() => setShowTemplateManager(true)}
          >
            Manage Templates
          </button>
        </div>
        <div className="empty-state">
          <p>No documents uploaded yet</p>
          <p className="empty-hint">Upload a ZIP file to get started</p>
        </div>
      </div>
    )
  }

  const categories = ['NDA', 'Employment', 'Vendor', 'MSA', 'SOW', 'Lease', 'Amendments', 'Service']

  return (
    <div className="document-list">
      <div className="document-list-header">
        <h3>Uploaded Documents ({documents.length})</h3>
        <button
          className="template-manager-toggle"
          onClick={() => setShowTemplateManager(true)}
        >
          Manage Templates
        </button>
      </div>
      <div className="documents-grid">
        {documents.map((doc) => {
          const template = isDocumentTemplate(doc.id)
          const isTemplate = !!template

          return (
            <div key={doc.id} className={`document-card ${isTemplate ? 'is-template' : ''}`}>
              <div className="document-icon">
                {getFileTypeIcon(doc.file_type)}
                {isTemplate && <span className="template-badge" title="Golden Template">⭐</span>}
              </div>
              <div className="document-info">
                <div className="document-name" title={doc.filename}>
                  {doc.filename}
                </div>
                <div className="document-meta">
                  <span className="file-size">{formatFileSize(doc.file_size)}</span>
                  <span className="file-type">{doc.file_type}</span>
                  <span className={`status status-${doc.status}`}>{doc.status}</span>
                  {isTemplate && (
                    <span
                      className="template-status"
                      style={{ color: getTemplateStatusBadge(template).color }}
                    >
                      Template: {getTemplateStatusBadge(template).text}
                    </span>
                  )}
                </div>
                <div className="document-date">{formatDate(doc.uploaded_at)}</div>
              </div>
              <div className="document-actions">
                {!isTemplate && (
                  <button
                    className="mark-template-button"
                    onClick={() => handleMarkAsTemplate(doc)}
                    title="Mark as template"
                  >
                    ⭐
                  </button>
                )}
                <button
                  className="delete-button"
                  onClick={() => handleDelete(doc.id, doc.filename)}
                  disabled={deleting === doc.id}
                  title="Delete document"
                >
                  {deleting === doc.id ? '⏳' : '🗑️'}
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {showTemplateModal && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Create Template</h3>
            <p className="modal-subtitle">Mark "{selectedDocument?.filename}" as a golden template</p>

            <form onSubmit={handleCreateTemplate}>
              <div className="form-group">
                <label htmlFor="category">Category *</label>
                <select
                  id="category"
                  value={templateCategory}
                  onChange={(e) => setTemplateCategory(e.target.value)}
                  required
                  disabled={creatingTemplate}
                >
                  <option value="">Select a category</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="notes">Notes (optional)</label>
                <textarea
                  id="notes"
                  value={templateNotes}
                  onChange={(e) => setTemplateNotes(e.target.value)}
                  placeholder="Add any notes about this template..."
                  rows={4}
                  disabled={creatingTemplate}
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="cancel-button"
                  onClick={handleCloseModal}
                  disabled={creatingTemplate}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="submit-button"
                  disabled={creatingTemplate}
                >
                  {creatingTemplate ? 'Creating...' : 'Create Template'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default DocumentList
