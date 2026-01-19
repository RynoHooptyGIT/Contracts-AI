import { useState, useEffect } from 'react'
import './TemplateManager.css'

function TemplateManager() {
  const [templates, setTemplates] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [processingId, setProcessingId] = useState(null)

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
        <button className="create-template-button">
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
    </div>
  )
}

export default TemplateManager
