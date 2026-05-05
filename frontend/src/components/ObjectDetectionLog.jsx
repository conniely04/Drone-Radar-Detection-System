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
    return Number.isFinite(speed) ? `${speed.toFixed(2)} m/s` : "—";
  };

  const formatRange = (detection) => {
    const range = Number(detection?.range ?? detection?.distance);
    if (Number.isFinite(range)) {
      return `${range.toFixed(2)} m`;
    }
    return "—";
  };

  const formatSensorTime = (detection) => {
    const sensorTime = Number(detection?.time);
    return Number.isFinite(sensorTime) ? `${sensorTime.toFixed(3)} s` : "—";
  };

  const latestSpeedDetection =
    detectionData.find((detection) => detection.speed != null) || latestDetection;
  const latestRangeDetection =
    detectionData.find(
      (detection) => detection.range != null || detection.distance != null,
    ) || latestDetection;

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
          <h4>Latest Radar Values</h4>
          <div className="detection-details">
            <div className="detail-item">
              <span className="label">Speed:</span>
              <span className="value speed">
                {formatSpeed(latestSpeedDetection)}
              </span>
            </div>
            <div className="detail-item">
              <span className="label">Range:</span>
              <span className="value">{formatRange(latestRangeDetection)}</span>
            </div>
            <div className="detail-item">
              <span className="label">Sensor Time:</span>
              <span className="value">
                {formatSensorTime(latestDetection)}
              </span>
            </div>
            <div className="detail-item">
              <span className="label">Received:</span>
              <span className="value">
                {formatTimestamp(latestDetection.timestamp)}
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
            <span>Received</span>
            <span>Sensor Time</span>
            <span>Speed</span>
            <span>Range</span>
          </div>
          {detectionData.length === 0 && !isLoading ? (
            <div className="no-data">No detections yet...</div>
          ) : (
            <div className="history-rows">
              {detectionData.slice().map((detection) => {
                return (
                  <div key={detection.id} className="history-row">
                    <span className="time" data-label="Received">
                      {formatTimestamp(detection.timestamp)}
                    </span>
                    <span className="sensor-time" data-label="Sensor Time">
                      {formatSensorTime(detection)}
                    </span>
                    <span className="speed" data-label="Speed">
                      {formatSpeed(detection)}
                    </span>
                    <span className="range" data-label="Range">
                      {formatRange(detection)}
                    </span>
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
