import { useState } from 'react';
import './AnnotationCard.css';

/**
 * AnnotationCard - Display individual change with accept/reject actions
 * Shows change type, risk level, original/suggested text, and rationale
 */
const AnnotationCard = ({ change, isSelected, onAccept, onReject }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [userAction, setUserAction] = useState(change.user_action);

  const {
    id,
    change_type,
    original_text,
    suggested_text,
    risk_level,
    rationale,
    start_offset,
    end_offset
  } = change;

  const handleAccept = () => {
    setUserAction('accepted');
    onAccept();
  };

  const handleReject = () => {
    setUserAction('rejected');
    onReject();
  };

  const getChangeTypeIcon = (type) => {
    switch (type) {
      case 'modification': return '✏️';
      case 'addition': return '➕';
      case 'deletion': return '➖';
      case 'missing_clause': return '❌';
      case 'extra_clause': return '🔵';
      default: return '📝';
    }
  };

  const getChangeTypeLabel = (type) => {
    switch (type) {
      case 'modification': return 'Modified';
      case 'addition': return 'Addition';
      case 'deletion': return 'Deletion';
      case 'missing_clause': return 'Missing Clause';
      case 'extra_clause': return 'Extra Clause';
      default: return 'Change';
    }
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'High': return '#dc2626';
      case 'Medium': return '#f59e0b';
      case 'Low': return '#16a34a';
      default: return '#6b7280';
    }
  };

  // Card status styling
  const cardStatusClass = userAction !== 'pending' ? `action-${userAction}` : '';
  const selectedClass = isSelected ? 'selected' : '';

  return (
    <div
      id={`annotation-card-${id}`}
      className={`annotation-card ${cardStatusClass} ${selectedClass} risk-${risk_level.toLowerCase()}`}
    >
      {/* Header */}
      <div className="card-header">
        <div className="card-header-left">
          <span className="change-icon">{getChangeTypeIcon(change_type)}</span>
          <span className="change-type-label">{getChangeTypeLabel(change_type)}</span>
          <span className="risk-badge" style={{ backgroundColor: getRiskColor(risk_level) }}>
            {risk_level}
          </span>
        </div>
        <div className="card-header-right">
          {userAction !== 'pending' && (
            <span className={`action-badge ${userAction}`}>
              {userAction === 'accepted' ? '✓ Accepted' : '✗ Rejected'}
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="card-content">
        {/* Modification: Show old → new */}
        {change_type === 'modification' && (
          <div className="diff-view">
            <div className="diff-old">
              <span className="diff-label">Original:</span>
              <span className="diff-text old-text">{original_text || '(empty)'}</span>
            </div>
            <span className="diff-arrow">→</span>
            <div className="diff-new">
              <span className="diff-label">Suggested:</span>
              <span className="diff-text new-text">{suggested_text || '(empty)'}</span>
            </div>
          </div>
        )}

        {/* Addition: Show new text */}
        {change_type === 'addition' && (
          <div className="single-text">
            <span className="text-label">Add:</span>
            <span className="text-content addition-text">{suggested_text}</span>
          </div>
        )}

        {/* Deletion: Show removed text */}
        {change_type === 'deletion' && (
          <div className="single-text">
            <span className="text-label">Remove:</span>
            <span className="text-content deletion-text">{original_text}</span>
          </div>
        )}

        {/* Missing Clause: Show template text */}
        {change_type === 'missing_clause' && (
          <div className="single-text">
            <span className="text-label">Template clause:</span>
            <span className="text-content missing-text">{suggested_text}</span>
          </div>
        )}

        {/* Extra Clause: Show contract text */}
        {change_type === 'extra_clause' && (
          <div className="single-text">
            <span className="text-label">Contract clause:</span>
            <span className="text-content extra-text">{original_text}</span>
          </div>
        )}

        {/* Rationale */}
        <div className={`rationale ${isExpanded ? 'expanded' : 'collapsed'}`}>
          <div className="rationale-header" onClick={() => setIsExpanded(!isExpanded)}>
            <span className="rationale-icon">💡</span>
            <span className="rationale-label">Rationale</span>
            <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
          </div>
          {isExpanded && (
            <div className="rationale-content">
              {rationale || 'No explanation provided'}
            </div>
          )}
        </div>

        {/* Position Info (for debugging) */}
        {isExpanded && (start_offset > 0 || end_offset > 0) && (
          <div className="position-info">
            <span className="position-label">Position:</span>
            <span className="position-value">{start_offset} - {end_offset}</span>
          </div>
        )}
      </div>

      {/* Actions */}
      {userAction === 'pending' && (
        <div className="card-actions">
          <button
            className="btn-accept"
            onClick={handleAccept}
            title="Accept this change"
          >
            ✓ Accept
          </button>
          <button
            className="btn-reject"
            onClick={handleReject}
            title="Reject this change"
          >
            ✗ Reject
          </button>
        </div>
      )}

      {/* Already actioned - show undo option */}
      {userAction !== 'pending' && (
        <div className="card-actions">
          <button
            className="btn-undo"
            onClick={() => setUserAction('pending')}
            title="Undo this action"
          >
            ↺ Undo
          </button>
        </div>
      )}
    </div>
  );
};

export default AnnotationCard;
