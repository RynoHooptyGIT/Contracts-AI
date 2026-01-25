import React, { useState } from 'react';
import './RedliningMode.css';
import AnnotatedDocumentPanel from './AnnotatedDocumentPanel';
import RedliningChat from './RedliningChat';
import ProgressModal from './ProgressModal';

/**
 * RedliningMode - Main container for contract redlining workflow
 *
 * Workflow Steps:
 * 1. Upload contract and select category
 * 2. Processing (extraction, matching, comparison)
 * 3. Results dashboard with risk score and deviations
 * 4. Clause-by-clause review
 * 5. Export redlined document
 */
const RedliningMode = ({ onExit }) => {
  const [currentStep, setCurrentStep] = useState('upload'); // upload, review
  const [sessionData, setSessionData] = useState(null);
  const [comparisons, setComparisons] = useState([]);
  const [loadingComparisons, setLoadingComparisons] = useState(false);

  // Progressive analysis state
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [progressiveChanges, setProgressiveChanges] = useState([]);
  const [summary, setSummary] = useState({ matched: 0, modified: 0, missing: 0, extra: 0 });
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [finalSummary, setFinalSummary] = useState(null);
  const [eventSource, setEventSource] = useState(null);
  const [highlightedClauseId, setHighlightedClauseId] = useState(null);

  // Progress modal state
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [processingStage, setProcessingStage] = useState('idle');
  const [processingError, setProcessingError] = useState(null);

  const steps = [
    { id: 'upload', label: 'Upload Contract', icon: '📤' },
    { id: 'review', label: 'Review', icon: '🔍' }
  ];

  const handleFileUpload = async (file, category) => {
    try {
      // Show progress modal and set initial stage
      setShowProgressModal(true);
      setProcessingStage('uploading');
      setProcessingError(null);

      console.log('🚀 [RedliningMode] Starting file upload:', file.name, 'Category:', category);

      // Step 1: Upload document
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', category);

      console.log('📤 [RedliningMode] Uploading to /api/documents/upload...');
      const uploadResponse = await fetch('http://localhost:8001/api/documents/upload', {
        method: 'POST',
        body: formData
      });

      console.log('✅ [RedliningMode] Upload response status:', uploadResponse.status);
      const uploadResult = await uploadResponse.json();
      console.log('📦 [RedliningMode] Upload result:', uploadResult);

      // Transition to matching stage
      setProcessingStage('matching');

      if (!uploadResult.success || !uploadResult.details || !uploadResult.details.documents || uploadResult.details.documents.length === 0) {
        console.error('❌ [RedliningMode] Upload validation failed:', uploadResult);
        throw new Error('Failed to upload document');
      }

      const documentId = uploadResult.details.documents[0].id;
      console.log('🆔 [RedliningMode] Document ID:', documentId);

      // Step 2: Start progressive redlining (returns immediately)
      console.log('🔄 [RedliningMode] Starting progressive redlining...');
      const sessionResponse = await fetch('http://localhost:8001/api/redlining/start-progressive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: documentId, category })
      });

      console.log('✅ [RedliningMode] Session response status:', sessionResponse.status);
      const sessionResult = await sessionResponse.json();
      console.log('📊 [RedliningMode] Session result:', sessionResult);

      if (!sessionResult.success) {
        throw new Error(sessionResult.detail || 'Failed to start progressive redlining');
      }

      // Transition to connecting stage
      setProcessingStage('connecting');

      // Store session data
      setSessionData(sessionResult);
      console.log('💾 [RedliningMode] Session data stored');

      // DO NOT move to review screen yet - will transition after analysis complete
      // setCurrentStep('review'); // COMMENTED OUT - transition happens in handleAnalysisComplete
      console.log('🎯 [RedliningMode] Moved to review step');

      // Step 3: Connect to SSE stream for progressive updates
      if (sessionResult.status === 'processing') {
        console.log('🌊 [RedliningMode] Connecting to SSE stream...');
        connectToProgressStream(sessionResult.session_id);

        // Transition to analyzing stage
        setProcessingStage('analyzing');
      } else {
        // No template found or other issue
        setAnalysisComplete(true);
        const errorMsg = sessionResult.message || 'No matching golden template found';
        setProcessingError(`${errorMsg}. We don't have a ${category} template in our golden templates database yet.`);
      }

    } catch (error) {
      console.error('❌ [RedliningMode] Error:', error);
      console.error('❌ [RedliningMode] Error stack:', error.stack);
      setProcessingError(error.message || 'Failed to process document');
      setProcessingStage('idle');
      // Modal will stay open showing error state with retry/cancel options
    }
  };

  const connectToProgressStream = (sessionId) => {
    console.log(`Connecting to SSE stream for session: ${sessionId}`);

    const es = new EventSource(`http://localhost:8001/api/redlining/session/${sessionId}/stream`);

    es.addEventListener('clause_compared', (event) => {
      try {
        const data = JSON.parse(event.data);
        handleClauseCompared(data);
      } catch (error) {
        console.error('Failed to parse clause_compared event:', error);
      }
    });

    es.addEventListener('complete', (event) => {
      try {
        const data = JSON.parse(event.data);
        handleAnalysisComplete(data);
        es.close();
      } catch (error) {
        console.error('Failed to parse complete event:', error);
      }
    });

    es.addEventListener('error', (event) => {
      console.error('SSE error:', event);
      if (event.data) {
        try {
          const data = JSON.parse(event.data);
          alert(`Analysis error: ${data.message}`);
        } catch (e) {
          console.error('Failed to parse error event:', e);
        }
      }
      es.close();
    });

    es.onerror = (error) => {
      console.error('EventSource failed:', error);
      es.close();
    };

    setEventSource(es);
  };

  const handleClauseCompared = (data) => {
    console.log('Clause compared:', data);

    // Highlight clause (will fade after 1 second)
    if (data.clause_id) {
      setHighlightedClauseId(data.clause_id);
      setTimeout(() => setHighlightedClauseId(null), 1000);
    }

    // Add changes to progressive changes list
    if (data.changes && data.changes.length > 0) {
      setProgressiveChanges(prev => [...prev, ...data.changes]);
    }

    // Update summary counts
    setSummary(prev => ({
      ...prev,
      [data.comparison_type]: (prev[data.comparison_type] || 0) + 1
    }));

    // Update progress
    if (data.progress) {
      setProgress(data.progress);
    }
  };

  const handleAnalysisComplete = (data) => {
    console.log('Analysis complete:', data);
    setAnalysisComplete(true);
    setFinalSummary(data);

    // Transition to complete stage
    setProcessingStage('complete');

    // Auto-dismiss modal after 2 seconds and transition to review screen
    setTimeout(() => {
      setShowProgressModal(false);
      setCurrentStep('review'); // NOW we transition to review screen
      setProcessingStage('idle');
    }, 2000);
  };

  const handleRetryUpload = () => {
    setShowProgressModal(false);
    setProcessingError(null);
    setProcessingStage('idle');
    // User can re-upload from upload screen
  };

  const handleCancelUpload = () => {
    setShowProgressModal(false);
    setProcessingError(null);
    setProcessingStage('idle');
    setCurrentStep('upload');
    // Close modal and reset to upload screen
  };

  // Cleanup EventSource on unmount
  React.useEffect(() => {
    return () => {
      if (eventSource) {
        console.log('Closing EventSource connection');
        eventSource.close();
      }
    };
  }, [eventSource]);

  const fetchComparisons = async () => {
    if (!sessionData || !sessionData.session_id) {
      console.error('No session data available');
      return;
    }

    setLoadingComparisons(true);
    try {
      const response = await fetch(
        `http://localhost:8001/api/redlining/session/${sessionData.session_id}/comparisons`
      );
      const result = await response.json();

      if (result.success) {
        setComparisons(result.comparisons || []);
      } else {
        throw new Error('Failed to fetch comparisons');
      }
    } catch (error) {
      console.error('Error fetching comparisons:', error);
      alert(`Error loading comparisons: ${error.message}`);
    } finally {
      setLoadingComparisons(false);
    }
  };

  const renderStepIndicator = () => (
    <div className="redlining-steps">
      {steps.map((step, index) => {
        const isActive = step.id === currentStep;
        const isPast = steps.findIndex(s => s.id === currentStep) > index;
        const stepClass = `step ${isActive ? 'active' : ''} ${isPast ? 'completed' : ''}`;

        return (
          <React.Fragment key={step.id}>
            <div className={stepClass}>
              <div className="step-icon">{step.icon}</div>
              <div className="step-label">{step.label}</div>
            </div>
            {index < steps.length - 1 && <div className="step-connector" />}
          </React.Fragment>
        );
      })}
    </div>
  );

  const renderUploadStep = () => (
    <div className="redlining-upload">
      <div className="upload-header">
        <h2>🔍 Contract Redlining</h2>
        <p>Upload a contract to compare against your golden templates</p>
      </div>

      <UploadForm onUpload={handleFileUpload} />

      <div className="upload-info">
        <div className="info-card">
          <span className="info-icon">✅</span>
          <div>
            <h4>Automatic Template Matching</h4>
            <p>We'll find the best matching golden template for your contract</p>
          </div>
        </div>
        <div className="info-card">
          <span className="info-icon">🎯</span>
          <div>
            <h4>Clause-by-Clause Analysis</h4>
            <p>Every clause is compared semantically using AI</p>
          </div>
        </div>
        <div className="info-card">
          <span className="info-icon">⚠️</span>
          <div>
            <h4>Risk Assessment</h4>
            <p>Deviations are analyzed and assigned risk levels</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderProcessingStep = () => (
    <div className="redlining-processing">
      <h2>⚙️ Processing Your Contract</h2>
      <p>This may take 30-60 seconds depending on document size</p>

      <div className="active-indicator">
        <div className="spinner"></div>
        <div className="status-messages">
          <p className="pulsing-text">Analyzing contract clauses</p>
          <p className="patience-note">This process may take 30-60 seconds</p>
        </div>
      </div>

      <div className="processing-stages">
        {Object.entries(processingStatus).map(([stage, status]) => (
          <div key={stage} className={`processing-stage ${status}`}>
            <div className="stage-icon">
              {status === 'completed' && '✅'}
              {status === 'in_progress' && '⏳'}
              {status === 'pending' && '○'}
            </div>
            <div className="stage-content">
              <h4>{stage.charAt(0).toUpperCase() + stage.slice(1)}</h4>
              <p className="stage-status">{status.replace('_', ' ')}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="progress-bar-container">
        <div className="progress-bar">
          <div className="progress-fill"></div>
        </div>
        <p className="progress-text">Processing... Please do not close this window</p>
      </div>
    </div>
  );

  const handleExport = async () => {
    if (!sessionData) return;

    try {
      const response = await fetch(
        `http://localhost:8001/api/redlining/session/${sessionData.session_id}/export`,
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

      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `redlined_contract_${sessionData.session_id.slice(0, 8)}.docx`;

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      console.log(`Successfully exported: ${filename}`);
    } catch (error) {
      console.error('Export error:', error);
      alert(`Failed to export document: ${error.message}`);
    }
  };

  const renderReviewStep = () => {
    if (loadingComparisons) {
      return (
        <div className="redlining-review">
          <h2>🔍 Loading Comparisons...</h2>
          <div className="spinner"></div>
        </div>
      );
    }

    if (!sessionData) {
      return (
        <div className="redlining-review">
          <p>No session data available</p>
          <button className="btn-secondary" onClick={() => setCurrentStep('results')}>
            ← Back to Results
          </button>
        </div>
      );
    }

    return (
      <div className="redlining-review-layout">
        {/* Compact Header with Stats */}
        <div className="review-compact-header">
          <div className="header-left">
            <span className="header-icon">📋</span>
            <h2>Visual Redlining Review</h2>
            <span className="session-badge">Session: {sessionData.session_id.substring(0, 8)}</span>
          </div>

          <div className="header-stats">
            {analysisComplete ? (
              <span className="stat-item">
                ✅ Complete | ✓{summary.matched} ~{summary.modified} ✗{summary.missing} +{summary.extra}
              </span>
            ) : (
              <span className="stat-item analyzing">
                Analyzing... {progress.current}/{progress.total} clauses | ✓{summary.matched} ~{summary.modified}
              </span>
            )}
          </div>

          <button className="export-button" onClick={handleExport}>
            📥 Export DOCX
          </button>
        </div>

        {/* Split Layout: Document (75%) + Chat (25%) */}
        <div className="redlining-split-layout">
          {/* Left: Document Panel (75%) */}
          <div className="document-panel-container">
            <AnnotatedDocumentPanel
              documentId={sessionData.uploaded_document_id}
              sessionId={sessionData.session_id}
              progressiveChanges={progressiveChanges}
              progress={progress}
              summary={summary}
              finalSummary={finalSummary}
              analysisComplete={analysisComplete}
              highlightedClauseId={highlightedClauseId}
            />
          </div>

          {/* Right: Chat Panel (25%) */}
          <div className="chat-panel-container">
            <RedliningChat
              documentId={sessionData.uploaded_document_id}
              sessionId={sessionData.session_id}
            />
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="redlining-mode">
      {/* Progress Modal - Shows during document processing */}
      <ProgressModal
        isOpen={showProgressModal}
        stage={processingStage}
        progress={progress}
        summary={summary}
        error={processingError}
        onRetry={handleRetryUpload}
        onCancel={handleCancelUpload}
      />

      <div className="redlining-header">
        <button className="exit-button" onClick={onExit} title="Exit Redlining Mode">
          ✕
        </button>
        {renderStepIndicator()}
      </div>

      <div className="redlining-content">
        {currentStep === 'upload' && renderUploadStep()}
        {currentStep === 'review' && renderReviewStep()}
      </div>
    </div>
  );
};

/**
 * UploadForm - File upload component with category selection
 */
const UploadForm = ({ onUpload }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('Employment');
  const [isDragging, setIsDragging] = useState(false);

  const categories = ['NDA', 'Employment', 'Vendor', 'MSA', 'SOW', 'Lease', 'Service'];

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleSubmit = () => {
    if (selectedFile && selectedCategory) {
      onUpload(selectedFile, selectedCategory);
    }
  };

  return (
    <div className="upload-form">
      <div
        className={`file-drop-zone ${isDragging ? 'dragging' : ''} ${selectedFile ? 'has-file' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-input').click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf,.docx,.txt,.zip"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />

        {selectedFile ? (
          <div className="selected-file">
            <span className="file-icon">📄</span>
            <div className="file-details">
              <div className="file-name">{selectedFile.name}</div>
              <div className="file-size">{(selectedFile.size / 1024).toFixed(1)} KB</div>
            </div>
            <button
              className="remove-file"
              onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
            >
              ✕
            </button>
          </div>
        ) : (
          <div className="drop-prompt">
            <span className="drop-icon">📤</span>
            <p>Drop contract here or click to browse</p>
            <span className="drop-hint">PDF, DOCX, TXT, or ZIP</span>
          </div>
        )}
      </div>

      <div className="category-selector">
        <label>Contract Category:</label>
        <div className="category-pills">
          {categories.map(cat => (
            <button
              key={cat}
              className={`category-pill ${selectedCategory === cat ? 'selected' : ''}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <button
        className="btn-primary upload-submit"
        disabled={!selectedFile || !selectedCategory}
        onClick={handleSubmit}
      >
        Start Redlining →
      </button>
    </div>
  );
};

export default RedliningMode;
