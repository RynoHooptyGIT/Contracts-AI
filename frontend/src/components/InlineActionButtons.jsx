import { useState } from 'react';
import './InlineActionButtons.css';

/**
 * InlineActionButtons - Floating action buttons that appear on hover
 * Shows green checkmark (Accept) and red X (Reject) buttons
 */
const InlineActionButtons = ({ changeId, position, onAccept, onReject, isVisible }) => {
  const [isProcessing, setIsProcessing] = useState(false);

  const handleAccept = async (e) => {
    e.stopPropagation();
    if (isProcessing) return;

    setIsProcessing(true);
    try {
      await onAccept(changeId);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async (e) => {
    e.stopPropagation();
    if (isProcessing) return;

    setIsProcessing(true);
    try {
      await onReject(changeId);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isVisible) return null;

  return (
    <div
      className="inline-action-buttons"
      style={{
        position: 'fixed',
        top: `${position.y}px`,
        left: `${position.x}px`,
        zIndex: 10000
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <button
        className="inline-action-btn accept-btn"
        onClick={handleAccept}
        disabled={isProcessing}
        title="Accept this change"
        aria-label="Accept change"
      >
        <span className="btn-icon">✓</span>
        <span className="btn-label">Accept</span>
      </button>
      <button
        className="inline-action-btn reject-btn"
        onClick={handleReject}
        disabled={isProcessing}
        title="Reject this change"
        aria-label="Reject change"
      >
        <span className="btn-icon">✗</span>
        <span className="btn-label">Reject</span>
      </button>
    </div>
  );
};

export default InlineActionButtons;
