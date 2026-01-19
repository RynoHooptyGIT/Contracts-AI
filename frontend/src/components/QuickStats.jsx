import './QuickStats.css'

function QuickStats({ stats }) {
  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return 'No uploads yet'
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`
    return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`
  }

  return (
    <div className="quick-stats">
      <div className="stat-card">
        <div className="stat-icon">📄</div>
        <div className="stat-content">
          <div className="stat-value">{stats.totalDocuments.toLocaleString()}</div>
          <div className="stat-label">Total Documents</div>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">🕒</div>
        <div className="stat-content">
          <div className="stat-value">{formatTimeAgo(stats.lastUpload)}</div>
          <div className="stat-label">Last Upload</div>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">💾</div>
        <div className="stat-content">
          <div className="stat-value">{formatBytes(stats.storageUsed)}</div>
          <div className="stat-label">Storage Used</div>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">📈</div>
        <div className="stat-content">
          <div className="stat-value">{stats.recentUploads}</div>
          <div className="stat-label">Last 7 Days</div>
        </div>
      </div>
    </div>
  )
}

export default QuickStats
