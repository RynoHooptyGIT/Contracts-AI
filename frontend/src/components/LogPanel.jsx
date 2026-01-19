import { useState, useEffect, useRef } from 'react'
import './LogPanel.css'

function LogPanel() {
  const [logs, setLogs] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const logsEndRef = useRef(null)
  const eventSourceRef = useRef(null)

  useEffect(() => {
    // Connect to log stream
    const eventSource = new EventSource('http://localhost:8001/api/logs/stream')
    eventSourceRef.current = eventSource

    eventSource.onopen = () => {
      setIsConnected(true)
      console.log('Connected to log stream')
    }

    eventSource.onmessage = (event) => {
      try {
        const logEntry = JSON.parse(event.data)
        setLogs(prev => [...prev, logEntry])
      } catch (error) {
        console.error('Failed to parse log entry:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error)
      setIsConnected(false)
      eventSource.close()

      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        window.location.reload()
      }, 3000)
    }

    // Cleanup on unmount
    return () => {
      eventSource.close()
    }
  }, [])

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const clearLogs = () => {
    setLogs([])
  }

  const formatTimestamp = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getLogClassName = (level) => {
    return `log-entry log-${level.toLowerCase()}`
  }

  return (
    <div className="log-panel">
      <div className="log-panel-header">
        <h3>System Logs</h3>
        <div className="log-panel-controls">
          <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '● Connected' : '○ Disconnected'}
          </span>
          <button onClick={clearLogs} className="clear-logs-btn">Clear</button>
        </div>
      </div>

      <div className="log-panel-content">
        {logs.length === 0 ? (
          <div className="log-empty">
            <p>Waiting for log messages...</p>
          </div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className={getLogClassName(log.level)}>
              <span className="log-timestamp">{formatTimestamp(log.timestamp)}</span>
              {log.context && <span className="log-context">[{log.context}]</span>}
              <span className="log-level">{log.level}</span>
              <span className="log-message">{log.message}</span>
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  )
}

export default LogPanel
