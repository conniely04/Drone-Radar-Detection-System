import React, { useState, useEffect } from "react";
import "./ObjectDetectionLog.css";

const ObjectDetectionLog = () => {
  const [detectionData, setDetectionData] = useState([]);
  const [latestDetection, setLatestDetection] = useState(null);
  const [backendUrl] = useState("http://localhost:5001");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch detections from backend API
  const fetchDetections = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(`${backendUrl}/api/detections`);

      if (!response.ok) {
        throw new Error("Failed to fetch detections");
      }

      const data = await response.json();
      setDetectionData(data.detections || []);
      setLatestDetection(data.latest);
    } catch (err) {
      console.error("Error fetching detections:", err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Add test detection via backend API
  const addTestDetection = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/sensor/test`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Failed to add test detection");
      }

      // Refresh the detections after adding test data
      await fetchDetections();
    } catch (err) {
      console.error("Error adding test detection:", err);
      setError(err.message);
    }
  };

  // Fetch real detection data and set up polling
  useEffect(() => {
    // Initial fetch
    fetchDetections();

    // Set up polling for real-time updates (every 5 seconds)
    const interval = setInterval(fetchDetections, 5000);

    return () => clearInterval(interval);
  }, []);

  const addManualDetection = async () => {
    await addTestDetection();
  };

  const formatTimestamp = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="detection-log-container">
      <div className="detection-header">
        <h3>Object Detection Log</h3>
        <div className="controls">
          <button
            onClick={addManualDetection}
            className="simulate-btn"
            disabled={isLoading}
          >
            {isLoading ? "Adding..." : "Add Test Detection"}
          </button>
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
              <span className="value speed">{latestDetection.speed} mph</span>
            </div>
            <div className="detail-item">
              <span className="label">Position:</span>
              <span className="value">{latestDetection.distance} ft away</span>
            </div>
            <div className="detail-item">
              <span className="label">Timestamp:</span>
              <span className="value">
                {formatTimestamp(latestDetection.timestamp)}
              </span>
            </div>
            <div className="detail-item">
              <span className="label">Object Type:</span>
              <span className="value">{latestDetection.object_type}</span>
            </div>
            <div className="detail-item">
              <span className="label">Confidence:</span>
              <span className="value">
                {(latestDetection.confidence * 100).toFixed(0)}%
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
            <span>Type</span>
            <span>Confidence</span>
          </div>
          {detectionData.length === 0 && !isLoading ? (
            <div className="no-data">
              No detections yet...
              <br />
              <small>Click "Add Test Detection" to generate sample data</small>
            </div>
          ) : (
            detectionData
              .slice()
              .reverse()
              .map((detection) => (
                <div key={detection.id} className="history-row">
                  <span className="time">
                    {formatTimestamp(detection.timestamp)}
                  </span>
                  <span className="speed">{detection.speed} mph</span>
                  <span className="distance">{detection.distance} ft</span>
                  <span className="type">{detection.object_type}</span>
                  <span className="confidence">
                    {(detection.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              ))
          )}
        </div>
      </div>
    </div>
  );
};

export default ObjectDetectionLog;
