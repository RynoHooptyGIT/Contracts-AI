import { useState, useEffect } from 'react'
import './MetricsPanel.css'

function MetricsPanel({ refreshTrigger }) {
  const [metrics, setMetrics] = useState({
    totalDocuments: 0,
    totalChunks: 0,
    storageUsed: 0,
    fileTypes: {}
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true)
        const response = await fetch('http://localhost:8001/api/documents/metrics')
        if (response.ok) {
          const data = await response.json()
          setMetrics(data)
        }
      } catch (error) {
        console.error('Failed to fetch metrics:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [refreshTrigger])

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  if (loading) {
    return (
      <div className="metrics-panel">
        <h3>System Metrics</h3>
        <div className="metrics-loading">Loading metrics...</div>
      </div>
    )
  }

  return (
    <div className="metrics-panel">
      <h3>📊 System Metrics</h3>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon">📄</div>
          <div className="metric-content">
            <div className="metric-value">{metrics.totalDocuments.toLocaleString()}</div>
            <div className="metric-label">Documents</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">🔢</div>
          <div className="metric-content">
            <div className="metric-value">{metrics.totalChunks.toLocaleString()}</div>
            <div className="metric-label">Text Chunks</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">💾</div>
          <div className="metric-content">
            <div className="metric-value">{formatBytes(metrics.storageUsed)}</div>
            <div className="metric-label">Storage Used</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">🔍</div>
          <div className="metric-content">
            <div className="metric-value">{metrics.vectorDimensions || 384}</div>
            <div className="metric-label">Vector Dimensions</div>
          </div>
        </div>
      </div>

      {Object.keys(metrics.fileTypes).length > 0 && (
        <div className="file-types-section">
          <h4>File Types</h4>
          <div className="file-types-grid">
            {Object.entries(metrics.fileTypes).map(([type, count]) => (
              <div key={type} className="file-type-item">
                <span className="file-type-ext">{type}</span>
                <span className="file-type-count">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default MetricsPanel
