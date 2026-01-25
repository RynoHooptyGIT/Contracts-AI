import { useState, useEffect } from 'react';
import './ColorLegendSidebar.css';

/**
 * ColorLegendSidebar - Fixed sidebar showing color meanings, progress, and live stats
 * Replaces the bottom ProgressiveSummaryPanel to maximize document viewing area
 */
const ColorLegendSidebar = ({ progress, summary, finalSummary, analysisComplete }) => {
  const progressPercent = progress.total > 0
    ? Math.round((progress.current / progress.total) * 100)
    : 0;

  const getRiskLevel = (score) => {
    if (!score) return 'N/A';
    if (score > 0.7) return 'High';
    if (score > 0.4) return 'Medium';
    return 'Low';
  };

  const getRiskColor = (score) => {
    if (!score) return '#666';
    if (score > 0.7) return '#dc2626';  // Red
    if (score > 0.4) return '#f59e0b';  // Amber
    return '#16a34a';  // Green
  };

  return (
    <div className="color-legend-sidebar">
      <h3>📊 Color Legend</h3>

      {/* Color Meanings */}
      <div className="legend-items">
        <div className="legend-item">
          <div className="legend-color green"></div>
          <div className="legend-text">
            <strong>Matched</strong>
            <span>Exact match</span>
          </div>
        </div>

        <div className="legend-item">
          <div className="legend-color yellow"></div>
          <div className="legend-text">
            <strong>Modified</strong>
            <span>Minor changes</span>
          </div>
        </div>

        <div className="legend-item">
          <div className="legend-color red"></div>
          <div className="legend-text">
            <strong>Critical</strong>
            <span>Major deviation</span>
          </div>
        </div>

        <div className="legend-item">
          <div className="legend-color blue"></div>
          <div className="legend-text">
            <strong>Missing</strong>
            <span>Not in document</span>
          </div>
        </div>

        <div className="legend-item">
          <div className="legend-color purple"></div>
          <div className="legend-text">
            <strong>Extra</strong>
            <span>Not in template</span>
          </div>
        </div>
      </div>

      <div className="legend-divider"></div>

      {/* Progress Bar */}
      <div className="legend-progress">
        <h4>Progress</h4>
        <div className="progress-text">
          {analysisComplete
            ? '✅ Complete'
            : `${progress.current}/${progress.total} clauses`
          }
        </div>
        <div className="progress-bar-container">
          <div
            className="progress-bar-fill"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      <div className="legend-divider"></div>

      {/* Live Stats */}
      <div className="legend-stats">
        <h4>Analysis Stats</h4>

        <div className="stat-row">
          <span className="stat-label">✓ Matched:</span>
          <span className="stat-value">{summary.matched || 0}</span>
        </div>

        <div className="stat-row">
          <span className="stat-label">~ Modified:</span>
          <span className="stat-value">{summary.modified || 0}</span>
        </div>

        <div className="stat-row">
          <span className="stat-label">✗ Missing:</span>
          <span className="stat-value">{summary.missing || 0}</span>
        </div>

        <div className="stat-row">
          <span className="stat-label">+ Extra:</span>
          <span className="stat-value">{summary.extra || 0}</span>
        </div>

        {analysisComplete && finalSummary && (
          <>
            <div className="legend-divider"></div>
            <div className="stat-row risk">
              <span className="stat-label">Overall Risk:</span>
              <span
                className="stat-value"
                style={{ color: getRiskColor(finalSummary.overall_risk_score) }}
              >
                {getRiskLevel(finalSummary.overall_risk_score)} ({Math.round((finalSummary.overall_risk_score || 0) * 100)}%)
              </span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Deviations:</span>
              <span className="stat-value">{finalSummary.deviation_count}</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ColorLegendSidebar;
