import { useState, useEffect } from 'react'
import './TemplateManager.css'

function TemplateManager() {
  const [templates, setTemplates] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [processingId, setProcessingId] = useState(null)

  // Create template modal state
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [documents, setDocuments] = useState([])
  const [loadingDocuments, setLoadingDocuments] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState('')
  const [newTemplateCategory, setNewTemplateCategory] = useState('')
  const [newTemplateNotes, setNewTemplateNotes] = useState('')
  const [creatingTemplate, setCreatingTemplate] = useState(false)

  const categories = ['All', 'NDA', 'Employment', 'Vendor', 'MSA', 'SOW', 'Lease', 'Amendments', 'Service']

  const fetchTemplates = async () => {
    setLoading(true)
    setError(null)

    try {
      const url = selectedCategory === 'All'
        ? 'http://localhost:8001/api/templates'
        : `http://localhost:8001/api/templates?category=${selectedCategory}`

      const response = await fetch(url)

      if (!response.ok) {
        throw new Error('Failed to fetch templates')
      }

      const data = await response.json()
      setTemplates(data.templates || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTemplates()
  }, [selectedCategory])

  const handleApprove = async (templateId, documentName) => {
    if (!confirm(`Are you sure you want to approve template "${documentName}"?`)) {
      return
    }

    setProcessingId(templateId)

    try {
      const response = await fetch(`http://localhost:8001/api/templates/${templateId}/approve`, {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error('Failed to approve template')
      }

      await fetchTemplates()
    } catch (err) {
      alert(`Failed to approve template: ${err.message}`)
    } finally {
      setProcessingId(null)
    }
  }

  const handleDeactivate = async (templateId, documentName) => {
    if (!confirm(`Are you sure you want to deactivate template "${documentName}"?`)) {
      return
    }

    setProcessingId(templateId)

    try {
      const response = await fetch(`http://localhost:8001/api/templates/${templateId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error('Failed to deactivate template')
      }

      await fetchTemplates()
    } catch (err) {
      alert(`Failed to deactivate template: ${err.message}`)
    } finally {
      setProcessingId(null)
    }
  }

  const handleOpenCreateModal = async () => {
    setShowCreateModal(true)
    setLoadingDocuments(true)

    try {
      const response = await fetch('http://localhost:8001/api/documents')

      if (!response.ok) {
        throw new Error('Failed to fetch documents')
      }

      const data = await response.json()

      // Fetch content preview for each document
      const docsWithPreviews = await Promise.all(
        (data.documents || []).map(async (doc) => {
          try {
            const contentResponse = await fetch(`http://localhost:8001/api/documents/${doc.id}`)
            if (contentResponse.ok) {
              const contentData = await contentResponse.json()
              // Get first 200 characters as preview
              const preview = contentData.content ? contentData.content.substring(0, 200) : ''
              return { ...doc, preview }
            }
          } catch {
            // If preview fetch fails, just return doc without preview
          }
          return { ...doc, preview: '' }
        })
      )

      setDocuments(docsWithPreviews)
    } catch (err) {
      alert(`Failed to load documents: ${err.message}`)
      setShowCreateModal(false)
    } finally {
      setLoadingDocuments(false)
    }
  }

  const handleCloseCreateModal = () => {
    setShowCreateModal(false)
    setSelectedDocument('')
    setNewTemplateCategory('')
    setNewTemplateNotes('')
  }

  const handleCreateTemplate = async () => {
    if (!selectedDocument) {
      alert('Please select a document')
      return
    }

    if (!newTemplateCategory) {
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
          document_id: selectedDocument,
          category: newTemplateCategory,
          notes: newTemplateNotes || null
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create template')
      }

      await fetchTemplates()
      handleCloseCreateModal()
      alert('Template created successfully!')
    } catch (err) {
      alert(`Failed to create template: ${err.message}`)
    } finally {
      setCreatingTemplate(false)
    }
  }

  const getStatusBadge = (template) => {
    if (template.is_approved && template.is_active) {
      return <span className="status-badge approved-active">Approved & Active</span>
    } else if (template.is_approved && !template.is_active) {
      return <span className="status-badge inactive">Inactive</span>
    } else {
      return <span className="status-badge pending">Pending Approval</span>
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A'
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const groupTemplatesByCategory = () => {
    const grouped = {}
    templates.forEach(template => {
      const category = template.category || 'Uncategorized'
      if (!grouped[category]) {
        grouped[category] = []
      }
      grouped[category].push(template)
    })
    return grouped
  }

  if (loading) {
    return (
      <div className="template-manager">
        <div className="template-header">
          <h2>Golden Template Management</h2>
        </div>
        <div className="loading">Loading templates...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="template-manager">
        <div className="template-header">
          <h2>Golden Template Management</h2>
        </div>
        <div className="error-message">{error}</div>
      </div>
    )
  }

  const groupedTemplates = groupTemplatesByCategory()

  return (
    <div className="template-manager">
      <div className="template-header">
        <h2>Golden Template Management</h2>
        <button className="create-template-button" onClick={handleOpenCreateModal}>
          + Create Template from Document
        </button>
      </div>

      <div className="category-tabs">
        {categories.map(category => (
          <button
            key={category}
            className={`category-tab ${selectedCategory === category ? 'active' : ''}`}
            onClick={() => setSelectedCategory(category)}
          >
            {category}
          </button>
        ))}
      </div>

      {templates.length === 0 ? (
        <div className="empty-state">
          <p>No templates found</p>
          <p className="empty-hint">Create templates from approved documents to get started</p>
        </div>
      ) : (
        <div className="templates-container">
          {selectedCategory === 'All' ? (
            Object.keys(groupedTemplates).sort().map(category => (
              <div key={category} className="category-section">
                <h3 className="category-title">{category}</h3>
                <div className="templates-grid">
                  {groupedTemplates[category].map(template => (
                    <div key={template.id} className="template-card">
                      <div className="template-card-header">
                        <div className="template-name" title={template.document_name}>
                          {template.document_name}
                        </div>
                        {getStatusBadge(template)}
                      </div>

                      <div className="template-metadata">
                        <div className="metadata-row">
                          <span className="metadata-label">Category:</span>
                          <span className="metadata-value">{template.category}</span>
                        </div>
                        <div className="metadata-row">
                          <span className="metadata-label">Version:</span>
                          <span className="metadata-value">{template.version || 'N/A'}</span>
                        </div>
                        <div className="metadata-row">
                          <span className="metadata-label">Created:</span>
                          <span className="metadata-value">{formatDate(template.created_at)}</span>
                        </div>
                        {template.approved_by && (
                          <div className="metadata-row">
                            <span className="metadata-label">Approved by:</span>
                            <span className="metadata-value">{template.approved_by}</span>
                          </div>
                        )}
                      </div>

                      <div className="template-actions">
                        {!template.is_approved && (
                          <button
                            className="action-button approve-button"
                            onClick={() => handleApprove(template.id, template.document_name)}
                            disabled={processingId === template.id}
                          >
                            {processingId === template.id ? 'Processing...' : 'Approve'}
                          </button>
                        )}
                        {template.is_active && (
                          <button
                            className="action-button deactivate-button"
                            onClick={() => handleDeactivate(template.id, template.document_name)}
                            disabled={processingId === template.id}
                          >
                            {processingId === template.id ? 'Processing...' : 'Deactivate'}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <div className="templates-grid">
              {templates.map(template => (
                <div key={template.id} className="template-card">
                  <div className="template-card-header">
                    <div className="template-name" title={template.document_name}>
                      {template.document_name}
                    </div>
                    {getStatusBadge(template)}
                  </div>

                  <div className="template-metadata">
                    <div className="metadata-row">
                      <span className="metadata-label">Category:</span>
                      <span className="metadata-value">{template.category}</span>
                    </div>
                    <div className="metadata-row">
                      <span className="metadata-label">Version:</span>
                      <span className="metadata-value">{template.version || 'N/A'}</span>
                    </div>
                    <div className="metadata-row">
                      <span className="metadata-label">Created:</span>
                      <span className="metadata-value">{formatDate(template.created_at)}</span>
                    </div>
                    {template.approved_by && (
                      <div className="metadata-row">
                        <span className="metadata-label">Approved by:</span>
                        <span className="metadata-value">{template.approved_by}</span>
                      </div>
                    )}
                  </div>

                  <div className="template-actions">
                    {!template.is_approved && (
                      <button
                        className="action-button approve-button"
                        onClick={() => handleApprove(template.id, template.document_name)}
                        disabled={processingId === template.id}
                      >
                        {processingId === template.id ? 'Processing...' : 'Approve'}
                      </button>
                    )}
                    {template.is_active && (
                      <button
                        className="action-button deactivate-button"
                        onClick={() => handleDeactivate(template.id, template.document_name)}
                        disabled={processingId === template.id}
                      >
                        {processingId === template.id ? 'Processing...' : 'Deactivate'}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create Template Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={handleCloseCreateModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Golden Template</h3>
              <button className="modal-close" onClick={handleCloseCreateModal}>×</button>
            </div>

            <div className="modal-body">
              {loadingDocuments ? (
                <div className="modal-loading">Loading documents...</div>
              ) : (
                <>
                  <div className="form-group">
                    <label>Select Document</label>
                    {documents.length === 0 ? (
                      <div className="no-documents">
                        No documents uploaded yet. Please upload documents first.
                      </div>
                    ) : (
                      <div className="document-list">
                        {documents.map(doc => (
                          <div
                            key={doc.id}
                            className={`document-card ${selectedDocument === doc.id ? 'selected' : ''}`}
                            onClick={() => setSelectedDocument(doc.id)}
                          >
                            <div className="document-card-header">
                              <input
                                type="radio"
                                name="document"
                                checked={selectedDocument === doc.id}
                                onChange={() => setSelectedDocument(doc.id)}
                                className="document-radio"
                              />
                              <div className="document-info">
                                <div className="document-filename">{doc.filename}</div>
                                <div className="document-meta">
                                  <span>{formatFileSize(doc.file_size)}</span>
                                  <span>•</span>
                                  <span>{formatDate(doc.uploaded_at)}</span>
                                </div>
                              </div>
                            </div>
                            {doc.preview && (
                              <div className="document-preview">
                                {doc.preview}...
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="form-group">
                    <label htmlFor="category-select">Category</label>
                    <select
                      id="category-select"
                      value={newTemplateCategory}
                      onChange={(e) => setNewTemplateCategory(e.target.value)}
                      className="form-select"
                    >
                      <option value="">-- Choose a category --</option>
                      {categories.filter(cat => cat !== 'All').map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="notes-input">Notes (Optional)</label>
                    <textarea
                      id="notes-input"
                      value={newTemplateNotes}
                      onChange={(e) => setNewTemplateNotes(e.target.value)}
                      className="form-textarea"
                      placeholder="Add any notes about this template..."
                      rows="4"
                    />
                  </div>
                </>
              )}
            </div>

            <div className="modal-footer">
              <button
                className="btn-secondary"
                onClick={handleCloseCreateModal}
                disabled={creatingTemplate}
              >
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={handleCreateTemplate}
                disabled={creatingTemplate || loadingDocuments}
              >
                {creatingTemplate ? 'Creating...' : 'Create Template'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TemplateManager
