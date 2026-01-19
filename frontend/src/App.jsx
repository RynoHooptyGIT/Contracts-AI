import { useState, useEffect } from 'react'
import './App.css'
import DocumentUpload from './components/DocumentUpload'
import DocumentList from './components/DocumentList'
import DocumentInsightsPanel from './components/DocumentInsightsPanel'
import MetricsPanel from './components/MetricsPanel'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [useRAG, setUseRAG] = useState(true)
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [showDocuments, setShowDocuments] = useState(false)
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
    // Trigger document list refresh
    setRefreshTrigger(prev => prev + 1)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    // Clear any previous errors
    setError('')

    // Input validation
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
      // Ollama returns { model, created_at, message: { role, content }, done, ... }
      const botMessage = data.message // { role: 'assistant', content: '...' }
      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      console.error('Error:', error)
      setError(error.message || 'Failed to send message. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-layout">
      <div className="main-content">
        <div className="app-container">
          <header>
            <h1>Contracts AI - Mistral Chat</h1>
            <div className="header-controls">
              <button
                className="toggle-documents-button"
                onClick={() => setShowDocuments(!showDocuments)}
              >
                {showDocuments ? '📖 Hide Documents' : '📁 Manage Documents'}
              </button>
              <div className="document-count-badge">
                <span className="badge-icon">📄</span>
                <span className="badge-count">{documentCount}</span>
                <span className="badge-label">Document{documentCount !== 1 ? 's' : ''} Indexed</span>
              </div>
              <label className="rag-toggle">
                <input
                  type="checkbox"
                  checked={useRAG}
                  onChange={(e) => setUseRAG(e.target.checked)}
                />
                <span className="toggle-label">Use Document Context (RAG)</span>
              </label>
            </div>
          </header>

          {showDocuments && (
            <div className="documents-section">
              <MetricsPanel refreshTrigger={refreshTrigger} />
              <DocumentUpload onUploadComplete={handleUploadComplete} />
              <DocumentList refreshTrigger={refreshTrigger} />
            </div>
          )}

          <div className="chat-container">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-content">
                  <strong>{msg.role === 'user' ? 'You' : 'Mistral'}:</strong>
                  <p>{msg.content}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="message assistant loading-message">
                <div className="message-content">
                  <strong>Mistral:</strong>
                  <p className="loading-dots">Thinking<span>.</span><span>.</span><span>.</span></p>
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="input-area">
            {error && <div className="error-message">{error}</div>}
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
            <button type="submit" disabled={loading || !input.trim()}>
              {loading ? 'Sending...' : 'Send'}
            </button>
          </form>
        </div>
      </div>

      <div className="log-panel-container">
        <DocumentInsightsPanel
          refreshTrigger={refreshTrigger}
          onQuestionClick={(question) => setInput(question)}
          onCategoryClick={(category) => {
            // Filter DocumentList by category
            console.log('Filter by category:', category)
            setShowDocuments(true)
          }}
        />
      </div>
    </div>
  )
}

export default App
