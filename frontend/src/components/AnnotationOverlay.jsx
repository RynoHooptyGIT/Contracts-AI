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
    if (progressiveChanges) {
      // Ensure all changes have user_action field (default to 'pending' if missing)
      const changesWithAction = progressiveChanges.map(change => ({
        ...change,
        user_action: change.user_action || 'pending'
      }));
      setChanges(changesWithAction);
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

    // Check if document has proper clause divs or if it's a single-div document
    const clauseDivs = container.querySelectorAll('[data-clause-id]');
    console.log(`Found ${clauseDivs.length} clause divs in document`);

    if (clauseDivs.length === 1) {
      // Fallback: Single div document - highlight based on text search
      console.log('Using text-search fallback for single-div document');
      const docDiv = clauseDivs[0];

      // Collect all highlight ranges first
      const highlightRanges = [];

      changes.forEach(change => {
        // Skip changes that don't exist in the uploaded document:
        // - missing_clause: not in uploaded doc
        // - deletion: template text that's missing from uploaded doc
        // - modification/addition: only highlight if original_text exists
        if (change.change_type === 'missing_clause' || change.change_type === 'deletion') {
          return;
        }

        // Only highlight if there's text from the uploaded document
        if (!change.original_text || change.original_text.length === 0) {
          console.log(`Skipping change ${change.id} - no original_text to highlight`);
          return;
        }

        // Find the text position
        const fullText = docDiv.textContent;
        const searchSnippet = change.original_text.substring(0, Math.min(100, change.original_text.length));
        const searchIndex = fullText.indexOf(searchSnippet);

        if (searchIndex !== -1) {
          const actualLength = Math.min(change.original_text.length, fullText.length - searchIndex);
          highlightRanges.push({
            id: change.id,
            start_offset: searchIndex,
            end_offset: searchIndex + actualLength,
            risk_level: change.risk_level,
            change_type: change.change_type
          });
          console.log(`✅ Found range for ${change.id} at ${searchIndex}-${searchIndex + actualLength}`);
        } else {
          console.warn(`Could not find text for change ${change.id} (${change.change_type})`);
        }
      });

      // Sort ranges by start position (descending) so we process from end to start
      // This prevents offset shifts as we modify the DOM
      highlightRanges.sort((a, b) => b.start_offset - a.start_offset);

      console.log(`📍 Applying ${highlightRanges.length} highlights in reverse order`);

      // Apply highlights from end to start
      highlightRanges.forEach(range => {
        highlightTextInElement(docDiv, range);
      });
    } else {
      // Standard path: Multi-div document with clause separation
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

      Object.entries(changesByClause).forEach(([clauseId, clauseChanges]) => {
        const clauseElement = container.querySelector(`[data-clause-id="${clauseId}"]`);

        if (!clauseElement) {
          console.warn(`Clause element not found for clause ID: ${clauseId}`);
          return;
        }

        clauseChanges.forEach(change => {
          highlightTextInElement(clauseElement, change);
        });
      });
    }
  };

  /**
   * Highlight specific text within a clause element
   * Uses character offsets to identify and wrap the target text
   */
  const highlightTextInElement = (element, change) => {
    const { id, start_offset, end_offset, risk_level, change_type } = change;

    console.log(`🔍 highlightTextInElement called for ${id}: offsets ${start_offset}-${end_offset}, type=${change_type}`);

    // Skip if no valid offsets
    if (start_offset === 0 && end_offset === 0 && change_type !== 'missing_clause') {
      console.log(`⏭️  Skipping ${id} - invalid offsets`);
      return;
    }

    // Get all text nodes within the element
    const textNodes = getTextNodes(element);
    console.log(`📝 Found ${textNodes.length} text nodes for highlighting`);

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
    console.log(`🎨 wrapTextInNode: ${changeId} at ${start}-${end}, text="${textNode.textContent.substring(start, end).substring(0, 30)}..."`);

    const text = textNode.textContent;
    const beforeText = text.slice(0, start);
    const highlightText = text.slice(start, end);
    const afterText = text.slice(end);

    // Create mark element
    const mark = document.createElement('mark');
    mark.className = `annotation-highlight risk-${riskLevel.toLowerCase()} type-${changeType}`;
    mark.dataset.changeId = changeId;
    mark.textContent = highlightText;

    console.log(`✨ Created mark element with class="${mark.className}", text="${highlightText.substring(0, 30)}..."`);

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
    console.log(`✅ DOM updated: replaced text node with fragment containing mark`);
  };

  /**
   * Highlight text by searching for it in the element (fallback for single-div documents)
   */
  const highlightByTextSearch = (element, change) => {
    const { id, original_text, suggested_text, risk_level, change_type } = change;

    // For extra_clause: use original_text (text that exists in uploaded doc)
    // For modification/missing_clause: use suggested_text (but it won't be found in uploaded doc - skip)
    const searchText = original_text || suggested_text;
    if (!searchText || searchText.length < 5) {
      return; // Too short to reliably search or no text available
    }

    // Get the full text content
    const fullText = element.textContent;

    // Search for the first 100 chars to find the position
    const searchSnippet = searchText.substring(0, Math.min(100, searchText.length));
    const searchIndex = fullText.indexOf(searchSnippet);

    if (searchIndex === -1) {
      console.warn(`Could not find text for change ${id} (${change_type}): "${searchText.substring(0, 30)}..."`);
      return;
    }

    // Calculate the actual end position based on full text length
    const actualLength = Math.min(searchText.length, fullText.length - searchIndex);

    console.log(`✅ Highlighting change ${id} at offset ${searchIndex}-${searchIndex + actualLength}`);

    // Find the exact text nodes at this position
    highlightTextInElement(element, {
      id,
      start_offset: searchIndex,
      end_offset: searchIndex + actualLength,
      risk_level,
      change_type
    });
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
        <div className="success-message">
          <div className="success-icon">✅</div>
          <h3>Perfect Match!</h3>
          <p>All clauses matched the golden template exactly. No changes needed.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="annotation-overlay">
      {/* Annotation Cards - Review Progress moved to ColorLegendSidebar */}
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
