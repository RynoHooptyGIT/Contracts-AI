import React, { useState, useEffect } from 'react';
import './ProgressModal.css';

/**
 * ProgressModal - Displays real-time progress during contract redlining processing
 *
 * Shows progression through stages:
 * 1. Uploading document
 * 2. Finding matching template
 * 3. Connecting to analysis stream
 * 4. Analyzing clauses (with live progress)
 * 5. Analysis complete
 *
 * Features:
 * - Full-screen blocking overlay during processing
 * - Real-time clause progress and statistics
 * - Error handling with retry/cancel options
 * - Auto-dismiss on completion
 * - Patience message for slow LLM processing
 */
const ProgressModal = ({ isOpen, stage, progress, summary, error, onRetry, onCancel }) => {
  const [showPatienceMessage, setShowPatienceMessage] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Track elapsed time for patience message
  useEffect(() => {
    if (!isOpen || stage === 'idle' || stage === 'complete') {
      setShowPatienceMessage(false);
      setElapsedTime(0);
      return;
    }

    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      setElapsedTime(elapsed);

      // Show patience message after 30 seconds on matching or analyzing stages
      if (elapsed >= 30 && (stage === 'matching' || stage === 'analyzing')) {
        setShowPatienceMessage(true);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isOpen, stage]);

  if (!isOpen) return null;

  // Define all processing stages with labels and icons
  const stages = [
    { id: 'uploading', label: 'Uploading document...', icon: '⬆️' },
    { id: 'matching', label: 'Finding matching template...', icon: '🔍' },
    { id: 'connecting', label: 'Connecting to analysis stream...', icon: '🌊' },
    { id: 'analyzing', label: 'Analyzing clauses', icon: '📊' },
    { id: 'complete', label: 'Analysis complete!', icon: '✅' }
  ];

  // Determine status of each stage (completed, active, or pending)
  const getStageStatus = (stageId) => {
    const currentIndex = stages.findIndex(s => s.id === stage);
    const stageIndex = stages.findIndex(s => s.id === stageId);

    if (stageIndex < currentIndex) return 'completed';
    if (stageIndex === currentIndex) return 'active';
    return 'pending';
  };

  // Calculate progress percentage for the progress bar
  const progressPercent = progress.total > 0
    ? Math.round((progress.current / progress.total) * 100)
    : 0;

  return (
    <div className="progress-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="progress-modal-title">
      <div className="progress-modal-content">
        {error ? (
          // Error State - Show error message with retry/cancel options
          <ErrorView error={error} onRetry={onRetry} onCancel={onCancel} />
        ) : (
          // Processing State - Show stage progression
          <>
            <h2 id="progress-modal-title">🔄 Processing Your Contract</h2>

            {/* Stage Checklist - Shows all stages with their status */}
            <div className="stage-list" role="status" aria-live="polite">
              {stages.map(s => (
                <StageItem
                  key={s.id}
                  label={s.label}
                  icon={s.icon}
                  status={getStageStatus(s.id)}
                  detail={s.id === 'analyzing' && stage === 'analyzing'
                    ? `(${progress.current}/${progress.total})`
                    : null}
                />
              ))}
            </div>

            {/* Patience Message - Shows after 30 seconds */}
            {showPatienceMessage && (
              <div className="patience-message">
                <div className="patience-icon">⏳</div>
                <div className="patience-content">
                  <p className="patience-title">Still processing...</p>
                  <p className="patience-detail">
                    {stage === 'matching' && 'AI is extracting clauses from your document. This can take 2-3 minutes for larger contracts.'}
                    {stage === 'analyzing' && 'Comparing clauses with AI. Large documents may take several minutes to analyze completely.'}
                  </p>
                  <p className="patience-time">Elapsed: {Math.floor(elapsedTime / 60)}:{(elapsedTime % 60).toString().padStart(2, '0')}</p>
                </div>
              </div>
            )}

            {/* Progress Bar - Only shown during analyzing stage */}
            {stage === 'analyzing' && progress.total > 0 && (
              <div className="modal-progress">
                <div className="progress-bar-container" role="progressbar" aria-valuenow={progressPercent} aria-valuemin="0" aria-valuemax="100">
                  <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }} />
                </div>
                <p className="progress-label">{progressPercent}% Complete</p>
              </div>
            )}

            {/* Live Stats - Only shown during analyzing stage with data */}
            {stage === 'analyzing' && (summary.matched > 0 || summary.modified > 0 || summary.missing > 0 || summary.extra > 0) && (
              <div className="modal-stats">
                <StatBadge label="Matched" value={summary.matched} color="green" icon="✓" />
                <StatBadge label="Modified" value={summary.modified} color="yellow" icon="~" />
                <StatBadge label="Missing" value={summary.missing} color="red" icon="✗" />
                <StatBadge label="Extra" value={summary.extra} color="blue" icon="+" />
              </div>
            )}

            {/* Completion Message - Only shown when complete */}
            {stage === 'complete' && (
              <p className="completion-message">
                Redirecting to review screen...
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
};

/**
 * StageItem - Individual stage in the checklist
 */
const StageItem = ({ label, icon, status, detail }) => (
  <div className={`stage-item ${status}`}>
    <span className={`stage-icon ${status}`}>
      {status === 'completed' && '✅'}
      {status === 'active' && '🔄'}
      {status === 'pending' && '○'}
    </span>
    <span className="stage-label">
      {label} {detail && <span className="stage-detail">{detail}</span>}
    </span>
  </div>
);

/**
 * StatBadge - Individual statistic badge (matched, modified, etc.)
 */
const StatBadge = ({ label, value, color, icon }) => (
  <div className={`stat-badge ${color}`}>
    <div className="stat-header">
      <span className="stat-icon">{icon}</span>
      <span className="stat-label">{label}</span>
    </div>
    <span className="stat-value">{value}</span>
  </div>
);

/**
 * ErrorView - Error state with retry/cancel options
 */
const ErrorView = ({ error, onRetry, onCancel }) => (
  <div className="error-view">
    <div className="error-header">
      <div className="error-icon">❌</div>
      <h2>Upload Failed</h2>
    </div>
    <div className="error-content">
      <p className="error-message">{error}</p>
      <p className="error-help">
        Please try uploading a different contract or select a different category.
      </p>
    </div>
    <div className="error-actions">
      <button className="btn-retry" onClick={onRetry}>
        🔄 Retry Upload
      </button>
      <button className="btn-cancel" onClick={onCancel}>
        ✕ Cancel
      </button>
    </div>
  </div>
);

export default ProgressModal;
