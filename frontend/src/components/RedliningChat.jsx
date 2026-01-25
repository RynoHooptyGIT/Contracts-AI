import { useState } from 'react';
import './RedliningChat.css';

/**
 * RedliningChat - Chat sidebar for asking questions during contract review
 * Context-aware chat that knows about the current document and session
 */
const RedliningChat = ({ documentId, sessionId }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const MAX_INPUT_LENGTH = 2000; // Shorter for sidebar

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError('');

    if (!input.trim()) {
      setError('Please enter a message');
      return;
    }

    if (input.length > MAX_INPUT_LENGTH) {
      setError(`Message too long (max ${MAX_INPUT_LENGTH} characters)`);
      return;
    }

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Build context-aware system message
      const systemContext = `You are an AI assistant helping review a contract. The user is currently reviewing a redlining session (ID: ${sessionId}) for document ${documentId}. Provide concise, helpful answers about contract clauses, legal terms, and redlining decisions.`;

      const contextualMessages = [
        { role: 'system', content: systemContext },
        ...messages,
        userMessage
      ];

      const url = new URL('http://localhost:8001/api/chat');
      url.searchParams.append('use_rag', 'true');
      url.searchParams.append('top_k', '3');

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: contextualMessages,
          model: 'mistral'
        }),
      });

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please wait a moment.');
        }
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      const botMessage = data.message;
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      setError(error.message || 'Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="redlining-chat">
      <div className="chat-header">
        <h3>💬 AI Assistant</h3>
        <p className="chat-subtitle">Ask questions while reviewing</p>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>Ask me questions about this contract:</p>
            <ul>
              <li>"What does this clause mean?"</li>
              <li>"Is this term standard?"</li>
              <li>"Should I accept this change?"</li>
            </ul>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-message ${msg.role}`}>
            <div className="message-header">
              <strong>{msg.role === 'user' ? 'You' : 'AI'}</strong>
            </div>
            <div className="message-text">
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="chat-message assistant loading">
            <div className="message-header">
              <strong>AI</strong>
            </div>
            <div className="message-text">
              <span className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </span>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        {error && <div className="chat-error">{error}</div>}

        <div className="chat-input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            disabled={loading}
            maxLength={MAX_INPUT_LENGTH}
            className="chat-input"
          />
          <button
            type="submit"
            className="chat-send-btn"
            disabled={loading || !input.trim()}
            title="Send message"
          >
            {loading ? '...' : '➤'}
          </button>
        </div>
        <div className="chat-char-count">{input.length}/{MAX_INPUT_LENGTH}</div>
      </form>
    </div>
  );
};

export default RedliningChat;
