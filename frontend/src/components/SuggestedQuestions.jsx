import './SuggestedQuestions.css'

function SuggestedQuestions({ questions, onQuestionClick }) {
  return (
    <div className="suggested-questions">
      <h3>💡 Suggested Questions</h3>
      <div className="questions-list">
        {questions && questions.length > 0 ? (
          questions.map((question, index) => (
            <button
              key={index}
              className="question-chip"
              onClick={() => onQuestionClick && onQuestionClick(question)}
              title={`Click to ask: ${question}`}
            >
              <span className="question-icon">💬</span>
              <span className="question-text">{question}</span>
            </button>
          ))
        ) : (
          <div className="no-questions">No suggestions available</div>
        )}
      </div>
    </div>
  )
}

export default SuggestedQuestions
