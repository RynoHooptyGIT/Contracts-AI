import { useState } from 'react'
import './ComplianceUpload.css'

function ComplianceUpload({ onUploadComplete }) {
  const [uploading, setUploading] = useState(false)
  const [complianceReport, setComplianceReport] = useState(null)
  const [error, setError] = useState('')
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = async (file) => {
    // Validate file type
    const allowedExtensions = ['.pdf', '.docx', '.txt', '.md']
    const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()

    if (!allowedExtensions.includes(fileExt)) {
      setError(`Unsupported file type. Allowed: ${allowedExtensions.join(', ')}`)
      return
    }

    setUploading(true)
    setError('')
    setComplianceReport(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8001/api/documents/compliance-check', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const report = await response.json()
        setComplianceReport(report)
        if (onUploadComplete) {
          onUploadComplete()
        }
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Compliance check failed')
      }
    } catch (err) {
      console.error('Compliance check error:', err)
      setError('Failed to check compliance. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="compliance-upload">
      <h3>🔍 Compliance Check</h3>
      <p className="compliance-description">
        Upload a contract to check compliance against standard templates
      </p>

      <div
        className={`upload-zone ${dragActive ? 'drag-active' : ''} ${uploading ? 'uploading' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-input').click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf,.docx,.txt,.md"
          onChange={handleFileInput}
          style={{ display: 'none' }}
        />
        {uploading ? (
          <div className="upload-status">
            <div className="spinner"></div>
            <div>Analyzing contract...</div>
          </div>
        ) : (
          <>
            <div className="upload-icon">📄</div>
            <div className="upload-text">
              <strong>Drop contract here</strong> or click to browse
            </div>
            <div className="upload-formats">PDF, DOCX, TXT, MD</div>
          </>
        )}
      </div>

      {error && (
        <div className="compliance-error">{error}</div>
      )}

      {complianceReport && (
        <div className="compliance-report">
          <div className="report-header">
            <h4>Compliance Report: {complianceReport.filename}</h4>
            <div className={`compliance-score ${complianceReport.compliance_score >= 0.7 ? 'good' : 'warning'}`}>
              Score: {(complianceReport.compliance_score * 100).toFixed(0)}%
            </div>
          </div>

          <div className="report-section">
            <h5>✅ Present Clauses</h5>
            <div className="clauses-list">
              {complianceReport.present_clauses.map((clause, index) => (
                <span key={index} className="clause-badge present">{clause}</span>
              ))}
            </div>
          </div>

          {complianceReport.missing_clauses && complianceReport.missing_clauses.length > 0 && (
            <div className="report-section">
              <h5>❌ Missing Clauses</h5>
              <div className="clauses-list">
                {complianceReport.missing_clauses.map((clause, index) => (
                  <span key={index} className="clause-badge missing">{clause}</span>
                ))}
              </div>
            </div>
          )}

          {complianceReport.unusual_terms && complianceReport.unusual_terms.length > 0 && (
            <div className="report-section">
              <h5>⚠️ Unusual Terms</h5>
              <div className="unusual-terms">
                {complianceReport.unusual_terms.map((term, index) => (
                  <div key={index} className="unusual-term">{term}</div>
                ))}
              </div>
            </div>
          )}

          <div className="report-section">
            <h5>📋 Recommendations</h5>
            <ul className="recommendations-list">
              {complianceReport.recommendations.map((rec, index) => (
                <li key={index}>{rec}</li>
              ))}
            </ul>
          </div>

          <div className="report-section">
            <h5>📚 Similar Contracts Found</h5>
            <div className="similar-contracts">
              {complianceReport.similar_contracts.map((contract, index) => (
                <div key={index} className="similar-contract">
                  <span className="contract-name">{contract.filename}</span>
                  <span className="similarity-score">
                    {(contract.similarity * 100).toFixed(0)}% similar
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ComplianceUpload
