import { useState, useEffect } from 'react';
import AnnotatedDocumentViewer from './AnnotatedDocumentViewer';
import './AnnotatedDocumentPanel.css';

/**
 * AnnotatedDocumentPanel - Wrapper for document viewer with header and actions
 * Displays the contract document with visual annotations and export controls
 * Supports progressive mode via progressiveChanges prop
 */
const AnnotatedDocumentPanel = ({
  documentId,
  sessionId,
  onExport,
  progressiveChanges,
  progress,
  summary,
  finalSummary,
  analysisComplete,
  highlightedClauseId
}) => {
  const [documentTitle, setDocumentTitle] = useState('');
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    // Fetch document metadata to get title
    const fetchDocumentInfo = async () => {
      try {
        const response = await fetch(`http://localhost:8001/api/documents/${documentId}`);
        if (response.ok) {
          const data = await response.json();
          setDocumentTitle(data.filename || 'Contract Document');
        }
      } catch (error) {
        console.error('Failed to fetch document info:', error);
        setDocumentTitle('Contract Document');
      } finally {
        setLoading(false);
      }
    };

    if (documentId) {
      fetchDocumentInfo();
    }
  }, [documentId]);

  return (
    <div className="annotated-document-panel">
      {/* Header */}
      <div className="document-panel-header">
        <div className="header-title">
          <h2>📄 {loading ? 'Loading...' : documentTitle}</h2>
          <span className="session-id">Session: {sessionId.slice(0, 8)}</span>
        </div>
        <div className="header-actions">
          {/* Export button will be added in Phase 4 */}
        </div>
      </div>

      {/* Document Content */}
      <div className="document-panel-content">
        <AnnotatedDocumentViewer
          documentId={documentId}
          sessionId={sessionId}
          progressiveChanges={progressiveChanges}
          progress={progress}
          summary={summary}
          finalSummary={finalSummary}
          analysisComplete={analysisComplete}
          highlightedClauseId={highlightedClauseId}
        />
      </div>

      {/* Footer - Export and other actions */}
      <div className="document-panel-footer">
        <div className="footer-info">
          <span className="info-icon">ℹ️</span>
          <span>Review annotations and accept/reject changes. Export when ready.</span>
        </div>
        <button
          className="export-button"
          onClick={handleExport}
          disabled={exporting}
          title="Export as DOCX with track changes"
        >
          {exporting ? (
            <>
              <span className="export-spinner">⏳</span>
              Exporting...
            </>
          ) : (
            <>
              <span className="export-icon">📥</span>
              Export DOCX
            </>
          )}
        </button>
      </div>
    </div>
  );

  async function handleExport() {
    try {
      setExporting(true);

      const response = await fetch(
        `http://localhost:8001/api/redlining/session/${sessionId}/export`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`);
      }

      // Get the blob from response
      const blob = await response.blob();

      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `redlined_contract_${sessionId.slice(0, 8)}.docx`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      console.log(`Successfully exported: ${filename}`);

      if (onExport) {
        onExport();
      }
    } catch (error) {
      console.error('Export error:', error);
      alert(`Failed to export document: ${error.message}`);
    } finally {
      setExporting(false);
    }
  }
};

export default AnnotatedDocumentPanel;
