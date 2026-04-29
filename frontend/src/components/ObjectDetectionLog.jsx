import React, { useState, useEffect } from "react";
import { backendUrl } from "../apiConfig";
import "./ObjectDetectionLog.css";

const ObjectDetectionLog = () => {
  const [detectionData, setDetectionData] = useState([]);
  const [latestDetection, setLatestDetection] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch detections from backend API
  const fetchDetections = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(`${backendUrl}/api/detections`);

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();
      setDetectionData(data.detections || []);
      setLatestDetection(data.latest);
    } catch (err) {
      console.error("Error fetching detections:", err);
      setError(`Cannot load detections from ${backendUrl}. Make sure the backend is running.`);
    } finally {
      setIsLoading(false);
    }
  };

  // (Removed) test detection endpoint - no fake data generation

  // Fetch real detection data and set up polling
  useEffect(() => {
    // Initial fetch
    fetchDetections();

    // Set up polling for real-time updates (every 5 seconds)
    const interval = setInterval(fetchDetections, 5000);

    return () => clearInterval(interval);
  }, []);

  // Manual detection generation removed

  const formatTimestamp = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const formatSpeed = (detection) => {
    const speed = Number(detection?.speed);
    return Number.isFinite(speed) ? Math.abs(speed).toFixed(2) : "—";
  };

  const formatDistance = (detection) => {
    if (detection?.computed_distance != null) {
      return `${Number(detection.computed_distance).toFixed(2)} ${
        detection.computed_distance_unit || detection.unit || ""
      }`;
    }
    if (detection?.distance != null) {
      return detection.distance;
    }
    return "—";
  };

  const formatDirection = (detection) => {
    const speed = Number(detection?.speed);
    if (speed < 0) return "Inbound";
    if (speed > 0) return "Outbound";
    return "—";
  };

  return (
    <div className="detection-log-container">
      <div className="detection-header">
        <h3>Object Detection Log</h3>
        <div className="controls">
          <button
            onClick={fetchDetections}
            className="refresh-btn"
            disabled={isLoading}
          >
            {isLoading ? "⟳" : "↻"} Refresh
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <span>⚠️ {error}</span>
        </div>
      )}

      {/* Loading Indicator */}
      {isLoading && (
        <div className="loading">
          <span>Loading detections...</span>
        </div>
      )}

      {/* Current Detection Display */}
      {latestDetection && (
        <div className="current-detection">
          <h4>Latest Detection</h4>
          <div className="detection-details">
            <div className="detail-item">
              <span className="label">Captured Speed:</span>
              <span className="value speed">{formatSpeed(latestDetection)}</span>
            </div>
            <div className="detail-item">
              <span className="label">Position:</span>
              <span className="value">{formatDistance(latestDetection)}</span>
            </div>
            <div className="detail-item">
              <span className="label">Timestamp:</span>
              <span className="value">
                {formatTimestamp(latestDetection.timestamp)}
              </span>
            </div>
            <div className="detail-item">
              <span className="label">Unit:</span>
              <span className="value">{latestDetection.unit || "—"}</span>
            </div>
            <div className="detail-item">
              <span className="label">Direction:</span>
              <span className="value direction">
                {formatDirection(latestDetection)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Detection History */}
      <div className="detection-history">
        <h4>Detection History ({detectionData.length} total)</h4>
        <div className="history-table">
          <div className="history-header">
            <span>Time</span>
            <span>Speed</span>
            <span>Distance</span>
            <span>Direction</span>
            <span>Unit</span>
          </div>
          {detectionData.length === 0 && !isLoading ? (
            <div className="no-data">No detections yet...</div>
          ) : (
            <div className="history-rows">
              {detectionData.slice().map((detection) => {
                return (
                  <div key={detection.id} className="history-row">
                    <span className="time">
                      {formatTimestamp(detection.timestamp)}
                    </span>
                    <span className="speed">{formatSpeed(detection)}</span>
                    <span className="distance">{formatDistance(detection)}</span>
                    <span className="direction">{formatDirection(detection)}</span>
                    <span className="unit">{detection.unit || "—"}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ObjectDetectionLog;
