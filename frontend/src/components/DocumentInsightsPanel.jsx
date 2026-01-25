import { useState, useEffect } from 'react'
import './DocumentInsightsPanel.css'
import QuickStats from './QuickStats'
import FileTypeBreakdown from './FileTypeBreakdown'
import CategoriesList from './CategoriesList'
import RecentActivityTimeline from './RecentActivityTimeline'
import CommonEntitiesList from './CommonEntitiesList'
import SuggestedQuestions from './SuggestedQuestions'
import ComplianceUpload from './ComplianceUpload'

function DocumentInsightsPanel({ refreshTrigger, onQuestionClick, onCategoryClick }) {
  const [insights, setInsights] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchInsights()
  }, [refreshTrigger])

  const fetchInsights = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await fetch('http://localhost:8001/api/documents/insights')
      if (response.ok) {
        const data = await response.json()
        setInsights(data)
      } else {
        setError('Failed to load insights')
      }
    } catch (err) {
      console.error('Failed to fetch insights:', err)
      setError('Failed to load insights')
    } finally {
      setLoading(false)
    }
  }

  if (loading && !insights) {
    return (
      <div className="insights-panel">
        <div className="insights-header">
          <h2>📊 Document Insights</h2>
        </div>
        <div className="insights-loading">Loading insights...</div>
      </div>
    )
  }

  if (error && !insights) {
    return (
      <div className="insights-panel">
        <div className="insights-header">
          <h2>📊 Document Insights</h2>
        </div>
        <div className="insights-error">{error}</div>
      </div>
    )
  }

  return (
    <div className="insights-panel">
      <div className="insights-header">
        <h2>📊 Document Insights</h2>
        <button
          className="help-button"
          title="View system documentation"
        >
          ?
        </button>
      </div>

      <div className="insights-content">
        {insights && (
          <>
            <QuickStats stats={insights.quickStats} />

            <FileTypeBreakdown
              fileTypes={insights.fileTypes}
              onTypeClick={(type) => console.log('Filter by type:', type)}
            />

            <CategoriesList
              categories={insights.categories}
              onCategoryClick={onCategoryClick}
            />

            <RecentActivityTimeline
              activity={insights.recentActivity}
            />

            <CommonEntitiesList
              entities={insights.commonEntities}
              onEntityClick={(entity) => console.log('Search entity:', entity)}
            />

            <SuggestedQuestions
              questions={insights.suggestedQuestions}
              onQuestionClick={onQuestionClick}
            />

            <ComplianceUpload onUploadComplete={fetchInsights} />
          </>
        )}
      </div>
    </div>
  )
}

export default DocumentInsightsPanel
