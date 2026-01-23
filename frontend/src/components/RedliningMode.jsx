import React, { useState } from 'react';
import './RedliningMode.css';
import AnnotatedDocumentViewer from './AnnotatedDocumentViewer';

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
  const [currentStep, setCurrentStep] = useState('upload'); // upload, processing, results, review
  const [sessionData, setSessionData] = useState(null);
  const [comparisons, setComparisons] = useState([]);
  const [loadingComparisons, setLoadingComparisons] = useState(false);
  const [reviewView, setReviewView] = useState('document'); // 'document' or 'comparison'
  const [processingStatus, setProcessingStatus] = useState({
    extraction: 'pending',
    matching: 'pending',
    comparison: 'pending',
    analysis: 'pending'
  });

  const steps = [
    { id: 'upload', label: 'Upload Contract', icon: '📤' },
    { id: 'processing', label: 'Processing', icon: '⚙️' },
    { id: 'results', label: 'Results', icon: '📊' },
    { id: 'review', label: 'Review', icon: '🔍' }
  ];

  const handleFileUpload = async (file, category) => {
    setCurrentStep('processing');

    try {
      // Step 1: Upload document
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', category);

      const uploadResponse = await fetch('http://localhost:8001/api/documents/upload', {
        method: 'POST',
        body: formData
      });

      const uploadResult = await uploadResponse.json();

      if (!uploadResult.success || uploadResult.details.documents.length === 0) {
        throw new Error('Failed to upload document');
      }

      const documentId = uploadResult.details.documents[0].id;

      // Step 2: Start redlining session
      setProcessingStatus(prev => ({ ...prev, extraction: 'in_progress' }));

      const sessionResponse = await fetch('http://localhost:8001/api/redlining/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: documentId, category })
      });

      const sessionResult = await sessionResponse.json();

      if (!sessionResult.success) {
        throw new Error(sessionResult.detail || 'Failed to start redlining session');
      }

      // Update processing status
      setProcessingStatus({
        extraction: 'completed',
        matching: 'completed',
        comparison: 'completed',
        analysis: 'completed'
      });

      // Store session data
      setSessionData(sessionResult);

      // Move to results
      setTimeout(() => setCurrentStep('results'), 500);

    } catch (error) {
      console.error('Redlining error:', error);
      alert(`Error: ${error.message}`);
      setCurrentStep('upload');
    }
  };

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

  const handleStartReview = async () => {
    setLoadingComparisons(true);
    await fetchComparisons();
    setCurrentStep('review');
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

  const renderResultsStep = () => {
    if (!sessionData) return null;

    // Provide defaults if summary is missing
    const summary = sessionData.summary || { matched: 0, modified: 0, missing: 0, extra: 0 };
    const riskScore = sessionData.overall_risk_score || 0;
    const matchScore = sessionData.template_match_score || 0;
    const deviationCount = sessionData.deviation_count || 0;

    const riskLevel = riskScore > 0.7 ? 'High' : riskScore > 0.4 ? 'Medium' : 'Low';
    const riskColor = riskLevel === 'High' ? '#ef4444' :
                      riskLevel === 'Medium' ? '#f59e0b' : '#10b981';

    return (
      <div className="redlining-results">
        <div className="results-header">
          <h2>📊 Redlining Results</h2>
          <button className="btn-secondary" onClick={onExit}>
            ← Back to Documents
          </button>
        </div>

        <div className="results-summary">
          <div className="summary-card risk-card">
            <div className="card-label">Overall Risk</div>
            <div className="card-value" style={{ color: riskColor }}>
              {riskLevel}
              <span className="risk-score">
                {(riskScore * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          <div className="summary-card">
            <div className="card-label">Template Match</div>
            <div className="card-value">
              {matchScore > 0 ? `${(matchScore * 100).toFixed(0)}%` : 'N/A'}
              <span className="card-subtext">{matchScore > 0 ? 'similarity' : 'no template'}</span>
            </div>
          </div>

          <div className="summary-card">
            <div className="card-label">Deviations Found</div>
            <div className="card-value">
              {deviationCount}
              <span className="card-subtext">differences</span>
            </div>
          </div>
        </div>

        <div className="results-breakdown">
          <h3>Clause Breakdown</h3>
          <div className="breakdown-grid">
            <div className="breakdown-item matched">
              <div className="item-count">{summary.matched}</div>
              <div className="item-label">✓ Matched</div>
            </div>
            <div className="breakdown-item modified">
              <div className="item-count">{summary.modified}</div>
              <div className="item-label">~ Modified</div>
            </div>
            <div className="breakdown-item missing">
              <div className="item-count">{summary.missing}</div>
              <div className="item-label">✗ Missing</div>
            </div>
            <div className="breakdown-item extra">
              <div className="item-count">{summary.extra}</div>
              <div className="item-label">+ Extra</div>
            </div>
          </div>
        </div>

        <div className="results-actions">
          <button
            className="btn-primary"
            onClick={handleStartReview}
            disabled={loadingComparisons}
          >
            {loadingComparisons ? 'Loading...' : 'Review Clause-by-Clause →'}
          </button>
          <button className="btn-secondary">
            Export Report
          </button>
        </div>
      </div>
    );
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

    // Group comparisons by type
    const grouped = {
      matched: comparisons.filter(c => c.comparison_type === 'matched'),
      modified: comparisons.filter(c => c.comparison_type === 'modified'),
      missing: comparisons.filter(c => c.comparison_type === 'missing'),
      extra: comparisons.filter(c => c.comparison_type === 'extra')
    };

    const getRiskColor = (level) => {
      switch (level) {
        case 'High': return '#ef4444';
        case 'Medium': return '#f59e0b';
        case 'Low': return '#10b981';
        default: return '#6b7280';
      }
    };

    return (
      <div className="redlining-review">
        <div className="review-header">
          <h2>🔍 Clause-by-Clause Review</h2>
          <div className="review-controls">
            <div className="view-toggle">
              <button
                className={reviewView === 'document' ? 'toggle-btn active' : 'toggle-btn'}
                onClick={() => setReviewView('document')}
              >
                📄 Document View
              </button>
              <button
                className={reviewView === 'comparison' ? 'toggle-btn active' : 'toggle-btn'}
                onClick={() => setReviewView('comparison')}
              >
                📋 Comparison Cards
              </button>
            </div>
            <button className="btn-secondary" onClick={() => setCurrentStep('results')}>
              ← Back to Results
            </button>
          </div>
        </div>

        <div className="review-content">
          {/* Document View - Visual Redlining */}
          {reviewView === 'document' && sessionData && (
            <div className="document-view-container">
              <AnnotatedDocumentViewer
                documentId={sessionData.uploaded_document_id}
                sessionId={sessionData.session_id}
              />
            </div>
          )}

          {/* Comparison Cards View */}
          {reviewView === 'comparison' && (
            <>
              {/* Matched Clauses */}
              {grouped.matched.length > 0 && (
            <div className="comparison-section matched-section">
              <h3>✓ Matched Clauses ({grouped.matched.length})</h3>
              {grouped.matched.map((comp) => (
                <div key={comp.id} className="comparison-card matched-card">
                  <div className="comparison-header">
                    <span className="comparison-icon">✓</span>
                    <div className="comparison-meta">
                      <span className="risk-badge" style={{ backgroundColor: getRiskColor(comp.risk_level) }}>
                        {comp.risk_level} Risk
                      </span>
                      <span className="similarity-score">
                        {(comp.similarity_score * 100).toFixed(0)}% match
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Modified Clauses */}
          {grouped.modified.length > 0 && (
            <div className="comparison-section modified-section">
              <h3>~ Modified Clauses ({grouped.modified.length})</h3>
              {grouped.modified.map((comp) => (
                <div key={comp.id} className="comparison-card modified-card">
                  <div className="comparison-header">
                    <span className="comparison-icon">~</span>
                    <div className="comparison-meta">
                      <span className="risk-badge" style={{ backgroundColor: getRiskColor(comp.risk_level) }}>
                        {comp.risk_level} Risk
                      </span>
                      <span className="similarity-score">
                        {(comp.similarity_score * 100).toFixed(0)}% match
                      </span>
                    </div>
                  </div>
                  {comp.deviation_summary && (
                    <div className="deviation-summary">
                      <strong>Deviation:</strong> {comp.deviation_summary}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Missing Clauses */}
          {grouped.missing.length > 0 && (
            <div className="comparison-section missing-section">
              <h3>✗ Missing Clauses ({grouped.missing.length})</h3>
              <p className="section-warning">These clauses are in the golden template but missing from your contract.</p>
              {grouped.missing.map((comp) => (
                <div key={comp.id} className="comparison-card missing-card">
                  <div className="comparison-header">
                    <span className="comparison-icon">✗</span>
                    <div className="comparison-meta">
                      <span className="risk-badge" style={{ backgroundColor: getRiskColor(comp.risk_level) }}>
                        {comp.risk_level} Risk
                      </span>
                    </div>
                  </div>
                  <div className="clause-note">Missing critical protection clause</div>
                </div>
              ))}
            </div>
          )}

          {/* Extra Clauses */}
          {grouped.extra.length > 0 && (
            <div className="comparison-section extra-section">
              <h3>+ Extra Clauses ({grouped.extra.length})</h3>
              <p className="section-info">These clauses are in your contract but not in the golden template.</p>
              {grouped.extra.map((comp) => (
                <div key={comp.id} className="comparison-card extra-card">
                  <div className="comparison-header">
                    <span className="comparison-icon">+</span>
                    <div className="comparison-meta">
                      <span className="risk-badge" style={{ backgroundColor: getRiskColor(comp.risk_level) }}>
                        {comp.risk_level} Risk
                      </span>
                    </div>
                  </div>
                  <div className="clause-note">Additional clause requires review</div>
                </div>
              ))}
            </div>
          )}

              {comparisons.length === 0 && (
                <div className="no-comparisons">
                  <p>No comparison data available</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="redlining-mode">
      <div className="redlining-header">
        <button className="exit-button" onClick={onExit} title="Exit Redlining Mode">
          ✕
        </button>
        {renderStepIndicator()}
      </div>

      <div className="redlining-content">
        {currentStep === 'upload' && renderUploadStep()}
        {currentStep === 'processing' && renderProcessingStep()}
        {currentStep === 'results' && renderResultsStep()}
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
