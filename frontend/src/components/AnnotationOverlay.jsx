import { useState, useEffect } from 'react';
import AnnotationCard from './AnnotationCard';
import './AnnotationOverlay.css';

/**
 * AnnotationOverlay - Manages and displays visual annotations on the document
 * Supports both progressive mode (via props) and batch mode (via API fetch)
 */
const AnnotationOverlay = ({ sessionId, documentContainerRef, onChangeAction, progressiveChanges }) => {
  const [changes, setChanges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedChangeId, setSelectedChangeId] = useState(null);

  // Progressive mode: Use changes from props
  useEffect(() => {
    if (progressiveChanges && progressiveChanges.length > 0) {
      setChanges(progressiveChanges);
      setLoading(false);
      console.log(`Using ${progressiveChanges.length} progressive changes`);
    }
  }, [progressiveChanges]);

  // Batch mode: Fetch individual changes from API
  useEffect(() => {
    // Skip API fetch if progressive changes are provided
    if (progressiveChanges) {
      return;
    }

    const fetchIndividualChanges = async () => {
      if (!sessionId) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await fetch(
          `http://localhost:8001/api/redlining/session/${sessionId}/individual-changes`
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch changes: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
          setChanges(data.changes || []);
          console.log(`Loaded ${data.change_count} individual changes from API`);
        } else {
          throw new Error('API returned success: false');
        }
      } catch (err) {
        console.error('Error fetching individual changes:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchIndividualChanges();
  }, [sessionId, progressiveChanges]);

  // Apply highlights to document after changes are loaded
  useEffect(() => {
    if (!documentContainerRef || !documentContainerRef.current || changes.length === 0) {
      return;
    }

    const container = documentContainerRef.current;
    applyHighlightsToDocument(container, changes);
  }, [changes, documentContainerRef]);

  /**
   * Apply visual highlights to the document based on changes
   * Uses start_offset and end_offset to wrap text in <mark> tags
   */
  const applyHighlightsToDocument = (container, changes) => {
    console.log('Applying highlights to document with', changes.length, 'changes');

    // Group changes by clause ID for efficient processing
    const changesByClause = {};
    changes.forEach(change => {
      const clauseId = change.new_clause_id || change.template_clause_id;
      if (clauseId) {
        if (!changesByClause[clauseId]) {
          changesByClause[clauseId] = [];
        }
        changesByClause[clauseId].push(change);
      }
    });

    // Apply highlights to each clause
    Object.entries(changesByClause).forEach(([clauseId, clauseChanges]) => {
      const clauseElement = container.querySelector(`[data-clause-id="${clauseId}"]`);

      if (!clauseElement) {
        console.warn(`Clause element not found for clause ID: ${clauseId}`);
        return;
      }

      // Apply highlights for each change in this clause
      clauseChanges.forEach(change => {
        highlightTextInElement(clauseElement, change);
      });
    });
  };

  /**
   * Highlight specific text within a clause element
   * Uses character offsets to identify and wrap the target text
   */
  const highlightTextInElement = (element, change) => {
    const { id, start_offset, end_offset, risk_level, change_type } = change;

    // Skip if no valid offsets
    if (start_offset === 0 && end_offset === 0 && change_type !== 'missing_clause') {
      return;
    }

    // Get all text nodes within the element
    const textNodes = getTextNodes(element);

    let currentOffset = 0;
    textNodes.forEach(node => {
      const nodeLength = node.textContent.length;
      const nodeStart = currentOffset;
      const nodeEnd = currentOffset + nodeLength;

      // Check if this node contains part of the target text
      if (nodeEnd >= start_offset && nodeStart <= end_offset) {
        const highlightStart = Math.max(0, start_offset - nodeStart);
        const highlightEnd = Math.min(nodeLength, end_offset - nodeStart);

        if (highlightStart < highlightEnd) {
          wrapTextInNode(node, highlightStart, highlightEnd, id, risk_level, change_type);
        }
      }

      currentOffset = nodeEnd;
    });
  };

  /**
   * Get all text nodes within an element
   */
  const getTextNodes = (element) => {
    const textNodes = [];
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          // Skip empty text nodes
          if (node.textContent.trim().length === 0) {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );

    let node;
    while (node = walker.nextNode()) {
      textNodes.push(node);
    }

    return textNodes;
  };

  /**
   * Wrap a portion of text in a node with a <mark> element
   */
  const wrapTextInNode = (textNode, start, end, changeId, riskLevel, changeType) => {
    const text = textNode.textContent;
    const beforeText = text.slice(0, start);
    const highlightText = text.slice(start, end);
    const afterText = text.slice(end);

    // Create mark element
    const mark = document.createElement('mark');
    mark.className = `annotation-highlight risk-${riskLevel.toLowerCase()} type-${changeType}`;
    mark.dataset.changeId = changeId;
    mark.textContent = highlightText;

    // Add click handler
    mark.addEventListener('click', () => {
      setSelectedChangeId(changeId);
      scrollToChange(changeId);
    });

    // Replace text node with fragments
    const fragment = document.createDocumentFragment();

    if (beforeText) {
      fragment.appendChild(document.createTextNode(beforeText));
    }

    fragment.appendChild(mark);

    if (afterText) {
      fragment.appendChild(document.createTextNode(afterText));
    }

    textNode.parentNode.replaceChild(fragment, textNode);
  };

  /**
   * Scroll to a specific change in the annotation cards panel
   */
  const scrollToChange = (changeId) => {
    const cardElement = document.getElementById(`annotation-card-${changeId}`);
    if (cardElement) {
      cardElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  };

  /**
   * Handle accept/reject actions from AnnotationCard
   */
  const handleChangeAction = async (changeId, action) => {
    try {
      // Update local state optimistically
      setChanges(prevChanges =>
        prevChanges.map(change =>
          change.id === changeId
            ? { ...change, user_action: action }
            : change
        )
      );

      // Call backend API to persist the action
      const response = await fetch(
        `http://localhost:8001/api/redlining/changes/${changeId}/action`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ action })
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to update change action: ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        console.log(`Successfully updated change ${changeId} to ${action}`);
        // Optionally notify parent component
        if (onChangeAction) {
          onChangeAction(changeId, action);
        }
      } else {
        throw new Error('API returned success: false');
      }
    } catch (error) {
      console.error('Error updating change action:', error);
      // Revert optimistic update on error
      setChanges(prevChanges =>
        prevChanges.map(change =>
          change.id === changeId
            ? { ...change, user_action: 'pending' }
            : change
        )
      );
      alert(`Failed to update change: ${error.message}`);
    }
  };

  // Group changes by risk level for display
  const changesByRisk = {
    High: changes.filter(c => c.risk_level === 'High' && c.user_action === 'pending'),
    Medium: changes.filter(c => c.risk_level === 'Medium' && c.user_action === 'pending'),
    Low: changes.filter(c => c.risk_level === 'Low' && c.user_action === 'pending')
  };

  const pendingCount = changes.filter(c => c.user_action === 'pending').length;
  const acceptedCount = changes.filter(c => c.user_action === 'accepted').length;
  const rejectedCount = changes.filter(c => c.user_action === 'rejected').length;

  if (loading) {
    return (
      <div className="annotation-overlay loading">
        <div className="loading-spinner"></div>
        <p>Loading annotations...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="annotation-overlay error">
        <p>Error loading annotations: {error}</p>
      </div>
    );
  }

  if (changes.length === 0) {
    return (
      <div className="annotation-overlay empty">
        <p>No annotations found for this session</p>
      </div>
    );
  }

  return (
    <div className="annotation-overlay">
      {/* Progress Summary */}
      <div className="annotation-summary">
        <h3>Review Progress</h3>
        <div className="progress-stats">
          <div className="stat pending">
            <span className="stat-count">{pendingCount}</span>
            <span className="stat-label">Pending</span>
          </div>
          <div className="stat accepted">
            <span className="stat-count">{acceptedCount}</span>
            <span className="stat-label">Accepted</span>
          </div>
          <div className="stat rejected">
            <span className="stat-count">{rejectedCount}</span>
            <span className="stat-label">Rejected</span>
          </div>
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${((acceptedCount + rejectedCount) / changes.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Annotation Cards */}
      <div className="annotation-cards-container">
        {/* High Risk Changes */}
        {changesByRisk.High.length > 0 && (
          <div className="annotation-section">
            <h4 className="section-title risk-high">⚠️ High Risk ({changesByRisk.High.length})</h4>
            {changesByRisk.High.map(change => (
              <AnnotationCard
                key={change.id}
                change={change}
                isSelected={selectedChangeId === change.id}
                onAccept={() => handleChangeAction(change.id, 'accepted')}
                onReject={() => handleChangeAction(change.id, 'rejected')}
              />
            ))}
          </div>
        )}

        {/* Medium Risk Changes */}
        {changesByRisk.Medium.length > 0 && (
          <div className="annotation-section">
            <h4 className="section-title risk-medium">⚡ Medium Risk ({changesByRisk.Medium.length})</h4>
            {changesByRisk.Medium.map(change => (
              <AnnotationCard
                key={change.id}
                change={change}
                isSelected={selectedChangeId === change.id}
                onAccept={() => handleChangeAction(change.id, 'accepted')}
                onReject={() => handleChangeAction(change.id, 'rejected')}
              />
            ))}
          </div>
        )}

        {/* Low Risk Changes */}
        {changesByRisk.Low.length > 0 && (
          <div className="annotation-section">
            <h4 className="section-title risk-low">✓ Low Risk ({changesByRisk.Low.length})</h4>
            {changesByRisk.Low.map(change => (
              <AnnotationCard
                key={change.id}
                change={change}
                isSelected={selectedChangeId === change.id}
                onAccept={() => handleChangeAction(change.id, 'accepted')}
                onReject={() => handleChangeAction(change.id, 'rejected')}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AnnotationOverlay;
