import './CategoriesList.css'

function CategoriesList({ categories, onCategoryClick }) {
  // Sort by count descending
  const sortedCategories = Object.entries(categories)
    .sort(([, a], [, b]) => b - a)

  const getCategoryIcon = (category) => {
    const icons = {
      'NDAs': '🤝',
      'Employment Agreements': '👔',
      'Vendor Contracts': '🏢',
      'Master Service Agreements': '📋',
      'Statements of Work': '📝',
      'Lease Agreements': '🏠',
      'Amendments': '✏️',
      'Service Agreements': '⚙️',
      'Uncategorized': '📄'
    }
    return icons[category] || '📄'
  }

  return (
    <div className="categories-list">
      <h3>🏷️ Document Categories</h3>
      <div className="category-items">
        {sortedCategories.map(([category, count]) => (
          <div
            key={category}
            className={`category-item ${category === 'Uncategorized' ? 'uncategorized' : ''}`}
            onClick={() => onCategoryClick && onCategoryClick(category)}
          >
            <div className="category-icon">{getCategoryIcon(category)}</div>
            <div className="category-info">
              <div className="category-name">{category}</div>
              <div className="category-count">{count} document{count !== 1 ? 's' : ''}</div>
            </div>
            {category === 'Uncategorized' && (
              <button
                className="tag-button"
                onClick={(e) => {
                  e.stopPropagation()
                  console.log('Tag uncategorized documents')
                }}
              >
                Tag
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default CategoriesList
