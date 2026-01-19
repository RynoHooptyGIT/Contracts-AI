import './FileTypeBreakdown.css'

function FileTypeBreakdown({ fileTypes, onTypeClick }) {
  // Calculate total for percentages
  const total = Object.values(fileTypes).reduce((sum, count) => sum + count, 0)

  // Sort by count descending
  const sortedTypes = Object.entries(fileTypes)
    .sort(([, a], [, b]) => b - a)

  const getTypeColor = (type) => {
    const colors = {
      '.pdf': '#ef4444',
      '.PDF': '#ef4444',
      '.docx': '#3b82f6',
      '.DOCX': '#3b82f6',
      '.txt': '#10b981',
      '.TXT': '#10b981',
      '.md': '#a855f7',
      '.MD': '#a855f7'
    }
    return colors[type] || '#6b7280'
  }

  return (
    <div className="file-type-breakdown">
      <h3>📁 File Types</h3>
      <div className="type-list">
        {sortedTypes.map(([type, count]) => {
          const percentage = ((count / total) * 100).toFixed(1)
          return (
            <div
              key={type}
              className="type-item"
              onClick={() => onTypeClick(type)}
            >
              <div className="type-header">
                <span className="type-name">{type}</span>
                <span className="type-count">
                  {count} ({percentage}%)
                </span>
              </div>
              <div className="type-bar-container">
                <div
                  className="type-bar"
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: getTypeColor(type)
                  }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default FileTypeBreakdown
