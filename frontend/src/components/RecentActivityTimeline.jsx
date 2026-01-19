import './RecentActivityTimeline.css'

function RecentActivityTimeline({ activity }) {
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A'
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <div className="recent-activity">
      <h3>📈 Recent Activity</h3>
      <div className="activity-stats">
        <div className="activity-item">
          <div className="activity-label">Last 7 days</div>
          <div className="activity-value">{activity.last7Days} uploads</div>
        </div>
        {activity.mostActiveDay && activity.mostActiveDay.count > 0 && (
          <div className="activity-item">
            <div className="activity-label">Most active day</div>
            <div className="activity-value">
              {formatDate(activity.mostActiveDay.date)} ({activity.mostActiveDay.count} docs)
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default RecentActivityTimeline
