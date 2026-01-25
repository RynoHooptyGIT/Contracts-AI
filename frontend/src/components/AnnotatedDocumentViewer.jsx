import React, { useState, useEffect, useRef } from 'react';
import DOMPurify from 'dompurify'; // XSS protection
import AnnotationOverlay from './AnnotationOverlay';
import ColorLegendSidebar from './ColorLegendSidebar';
import './AnnotatedDocumentViewer.css';

/**
 * Annotated Document Viewer
 *
 * Displays HTML-rendered documents with color-coded annotations overlaid on text
 * Supports click-to-view details and accept/reject individual changes
 * Uses DOMPurify to sanitize HTML and prevent XSS attacks
 *
 * SECURITY NOTE: This component uses DOMPurify.sanitize() with a strict whitelist
 * of allowed tags and attributes before rendering any HTML content. The sanitization
 * happens on line 50-58 before the content is stored in state.
 */
export default function AnnotatedDocumentViewer({
  documentId,
  sessionId,
  progressiveChanges,
  progress,
  summary,
  finalSummary,
  analysisComplete,
  highlightedClauseId
}) {
  const [htmlContent, setHtmlContent] = useState('');
  const [cssContent, setCssContent] = useState('');
  const [clauseMarkers, setClauseMarkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const docContainerRef = useRef(null);

  // Fetch rendered HTML document
  useEffect(() => {
    async function loadDocument() {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`http://localhost:8001/api/documents/${documentId}/render-html`);

        if (!response.ok) {
          throw new Error(`Failed to render document: ${response.statusText}`);
        }

        const data = await response.json();

        if (!data.success) {
          throw new Error(data.detail || 'Failed to render document');
        }

        // SECURITY: Sanitize HTML to prevent XSS attacks
        // Content is already sanitized on the backend with bleach.clean(),
        // but we apply DOMPurify as a second layer of defense
        const sanitizedHTML = DOMPurify.sanitize(data.html_content, {
          ALLOWED_TAGS: [
            'p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br',
            'strong', 'em', 'u', 'ol', 'ul', 'li', 'table', 'tr', 'td', 'th'
          ],
          ALLOWED_ATTR: ['class', 'data-clause-id', 'data-clause-type', 'data-clause-index']
        });

        setHtmlContent(sanitizedHTML);
        setCssContent(data.css_content || '');
        setClauseMarkers(data.clause_markers || []);
        setLoading(false);
      } catch (err) {
        console.error('Document rendering error:', err);
        setError(err.message);
        setLoading(false);
      }
    }

    if (documentId) {
      loadDocument();
    }
  }, [documentId]);

  // Apply highlight effect to clause element when highlightedClauseId changes
  useEffect(() => {
    if (!highlightedClauseId || !docContainerRef.current) return;

    const clauseElement = docContainerRef.current.querySelector(
      `[data-clause-id="${highlightedClauseId}"]`
    );

    if (clauseElement) {
      // Add highlighting class
      clauseElement.classList.add('clause-analyzing');

      // Remove after animation completes
      setTimeout(() => {
        clauseElement.classList.remove('clause-analyzing');
      }, 1000);

      // Scroll clause into view
      clauseElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [highlightedClauseId]);

  if (loading) {
    return (
      <div className="annotated-document-viewer">
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Rendering document...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="annotated-document-viewer">
        <div className="error-message">
          <h3>Error Loading Document</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  // htmlContent is already sanitized with DOMPurify before being set in state
  // This is safe to render
  const renderSanitizedHTML = () => {
    return { __html: htmlContent };
  };

  return (
    <div className="annotated-document-viewer">
      {/* Document Content */}
      <div className="document-content">
        {/* Inject document-specific CSS */}
        {cssContent && <style>{cssContent}</style>}

        {/* Render HTML that was sanitized on lines 50-58 with DOMPurify */}
        <div
          ref={docContainerRef}
          className="rendered-document"
          dangerouslySetInnerHTML={renderSanitizedHTML()}
        />
      </div>

      {/* Color Legend Sidebar */}
      <ColorLegendSidebar
        progress={progress}
        summary={summary}
        finalSummary={finalSummary}
        analysisComplete={analysisComplete}
      />

      {/* Annotation Overlay - Visual annotations with accept/reject */}
      {sessionId && (
        <AnnotationOverlay
          sessionId={sessionId}
          documentContainerRef={docContainerRef}
          progressiveChanges={progressiveChanges}
          onChangeAction={(changeId, action) => {
            console.log(`Change ${changeId} action: ${action}`);
            // API call will be implemented in Phase 3
          }}
        />
      )}
    </div>
  );
}
