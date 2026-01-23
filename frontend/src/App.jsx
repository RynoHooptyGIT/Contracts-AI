import { useState, useEffect } from 'react'
import './App.css'
import DocumentUpload from './components/DocumentUpload'
import DocumentList from './components/DocumentList'
import DocumentInsightsPanel from './components/DocumentInsightsPanel'
import MetricsPanel from './components/MetricsPanel'
import RedliningMode from './components/RedliningMode'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [useRAG, setUseRAG] = useState(true)
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [currentMode, setCurrentMode] = useState('chat') // 'chat', 'documents', 'redlining'
  const [documentCount, setDocumentCount] = useState(0)

  const MAX_INPUT_LENGTH = 4000

  // Fetch document count on mount and when refreshTrigger changes
  useEffect(() => {
    const fetchDocumentCount = async () => {
      try {
        const response = await fetch('http://localhost:8001/api/documents')
        if (response.ok) {
          const data = await response.json()
          setDocumentCount(data.count || 0)
        }
      } catch (error) {
        console.error('Failed to fetch document count:', error)
      }
    }

    fetchDocumentCount()
  }, [refreshTrigger])

  const handleUploadComplete = () => {
    setRefreshTrigger(prev => prev + 1)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    setError('')

    if (!input.trim()) {
      setError('Please enter a message')
      return
    }

    if (input.length > MAX_INPUT_LENGTH) {
      setError(`Message too long (max ${MAX_INPUT_LENGTH} characters)`)
      return
    }

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const url = new URL('http://localhost:8001/api/chat')
      url.searchParams.append('use_rag', useRAG)
      url.searchParams.append('top_k', '3')

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          model: 'mistral'
        }),
      })

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please wait a moment and try again.')
        }
        throw new Error(`Server error: ${response.status}`)
      }

      const data = await response.json()
      const botMessage = data.message
      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      console.error('Error:', error)
      setError(error.message || 'Failed to send message. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // If in redlining mode, render only RedliningMode
  if (currentMode === 'redlining') {
    return <RedliningMode onExit={() => setCurrentMode('chat')} />
  }

  return (
    <div className="app-layout">
      {/* Top Navigation Bar */}
      <nav className="top-nav">
        <div className="nav-brand">
          <span className="nav-brand-icon">⚖️</span>
          <h1>Contracts AI</h1>
        </div>

        <div className="nav-modes">
          <button
            className={`mode-button ${currentMode === 'chat' ? 'active' : ''}`}
            onClick={() => setCurrentMode('chat')}
          >
            <span className="icon">💬</span>
            Chat
          </button>
          <button
            className={`mode-button ${currentMode === 'documents' ? 'active' : ''}`}
            onClick={() => setCurrentMode('documents')}
          >
            <span className="icon">📁</span>
            Documents
          </button>
          <button
            className="mode-button"
            onClick={() => setCurrentMode('redlining')}
          >
            <span className="icon">🔍</span>
            Redlining
          </button>
        </div>

        <div className="nav-controls">
          <div className="document-badge">
            <span>📄</span>
            <span className="badge-count">{documentCount}</span>
            <span>Indexed</span>
          </div>

          <label className="rag-toggle">
            <input
              type="checkbox"
              checked={useRAG}
              onChange={(e) => setUseRAG(e.target.checked)}
            />
            <span className="toggle-label">Use RAG</span>
          </label>
        </div>
      </nav>

      {/* Main Content Area */}
      <div className="main-container">
        {/* Chat Section */}
        <div className="chat-section">
          {/* Document Management (shown when in documents mode) */}
          {currentMode === 'documents' && (
            <div className="documents-panel">
              <MetricsPanel refreshTrigger={refreshTrigger} />
              <DocumentUpload onUploadComplete={handleUploadComplete} />
              <DocumentList refreshTrigger={refreshTrigger} />
            </div>
          )}

          {/* Chat Container */}
          <div className="chat-container">
            {messages.length === 0 && (
              <div className="message assistant">
                <div className="message-content">
                  <strong>Mistral</strong>
                  <p>Hello! I'm your AI assistant for contract analysis. I can help you understand contracts, answer questions about your documents, and provide insights. How can I help you today?</p>
                </div>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-content">
                  <strong>{msg.role === 'user' ? 'You' : 'Mistral'}</strong>
                  <p>{msg.content}</p>
                </div>
              </div>
            ))}

            {loading && (
              <div className="message assistant loading-message">
                <div className="message-content">
                  <strong>Mistral</strong>
                  <p className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <form onSubmit={handleSubmit} className="input-area">
            {error && <div className="error-message">{error}</div>}

            <div className="input-container">
              <div className="input-group">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask something about contracts..."
                  disabled={loading}
                  maxLength={MAX_INPUT_LENGTH}
                />
                <span className="character-count">{input.length}/{MAX_INPUT_LENGTH}</span>
              </div>
              <button
                type="submit"
                className="send-button"
                disabled={loading || !input.trim()}
              >
                {loading ? 'Sending...' : 'Send'}
              </button>
            </div>
          </form>
        </div>

        {/* Side Panel - Document Insights */}
        <div className="side-panel">
          <div className="insights-panel">
            <DocumentInsightsPanel
              refreshTrigger={refreshTrigger}
              onQuestionClick={(question) => setInput(question)}
              onCategoryClick={(category) => {
                console.log('Filter by category:', category)
                setCurrentMode('documents')
              }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
