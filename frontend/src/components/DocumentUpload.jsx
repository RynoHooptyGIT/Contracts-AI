import { useState } from 'react'
import './DocumentUpload.css'

function DocumentUpload({ onUploadComplete }) {
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState(null)
  const [dragActive, setDragActive] = useState(false)

  const handleFileUpload = async (file) => {
    if (!file) return

    if (!file.name.endsWith('.zip')) {
      setUploadStatus({
        success: false,
        message: 'Please select a ZIP file containing your documents'
      })
      return
    }

    setUploading(true)
    setUploadStatus(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8001/api/documents/upload', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please wait a moment and try again.')
        }
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const result = await response.json()
      setUploadStatus({
        success: true,
        message: result.message,
        details: result.details
      })

      // Notify parent component
      if (onUploadComplete) {
        onUploadComplete()
      }
    } catch (error) {
      setUploadStatus({
        success: false,
        message: error.message || 'Upload failed. Please try again.'
      })
    } finally {
      setUploading(false)
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    handleFileUpload(file)
  }

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
      handleFileUpload(e.dataTransfer.files[0])
    }
  }

  return (
    <div className="document-upload">
      <h3>Upload Documents</h3>
      <p className="upload-description">
        Upload a ZIP file containing your documents (TXT, MD, PDF, DOCX)
      </p>

      <div
        className={`upload-area ${dragActive ? 'drag-active' : ''} ${uploading ? 'uploading' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          accept=".zip"
          onChange={handleFileChange}
          disabled={uploading}
          style={{ display: 'none' }}
        />
        <label htmlFor="file-upload" className="upload-label">
          {uploading ? (
            <>
              <div className="upload-spinner"></div>
              <p>Processing documents...</p>
            </>
          ) : (
            <>
              <div className="upload-icon">📁</div>
              <p>
                <strong>Click to upload</strong> or drag and drop
              </p>
              <p className="upload-hint">ZIP files only</p>
            </>
          )}
        </label>
      </div>

      {uploadStatus && (
        <div className={`upload-status ${uploadStatus.success ? 'success' : 'error'}`}>
          <p>{uploadStatus.message}</p>
          {uploadStatus.details && uploadStatus.details.errors && uploadStatus.details.errors.length > 0 && (
            <details className="error-details">
              <summary>Show errors ({uploadStatus.details.errors.length})</summary>
              <ul>
                {uploadStatus.details.errors.map((error, idx) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}
    </div>
  )
}

export default DocumentUpload
