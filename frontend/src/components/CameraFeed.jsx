import React, { useState, useEffect } from "react";
import "./CameraFeed.css";

const CameraFeed = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [backendUrl] = useState("http://localhost:5001");

  // Placeholder for when camera is not connected
  const placeholderImage =
    "data:image/svg+xml,%3Csvg width='640' height='480' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='100%25' height='100%25' fill='%23333'/%3E%3Ctext x='50%25' y='50%25' font-size='20' fill='white' text-anchor='middle' dy='.3em'%3ERaspberry Pi Camera Feed%3C/text%3E%3Ctext x='50%25' y='60%25' font-size='14' fill='%23ccc' text-anchor='middle' dy='.3em'%3E(Click Connect to Backend)%3C/text%3E%3C/svg%3E";

  // Check system status on component mount
  useEffect(() => {
    checkSystemStatus();
  }, []);

  const checkSystemStatus = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/system/status`);
      const status = await response.json();
      setSystemStatus(status);
    } catch (error) {
      console.error("Failed to check system status:", error);
    }
  };

  const handleConnect = async () => {
    try {
      // Start the backend system if not running
      if (systemStatus && !systemStatus.is_running) {
        await fetch(`${backendUrl}/api/system/start`, { method: "POST" });
      }

      setIsConnected(true);
      await checkSystemStatus();
    } catch (error) {
      console.error("Failed to connect to backend:", error);
      alert(
        "Failed to connect to backend. Make sure the backend server is running.",
      );
    }
  };

  const handleDisconnect = async () => {
    setIsConnected(false);
    await checkSystemStatus();
  };

  const addTestData = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/sensor/test`, {
        method: "POST",
      });
      const testData = await response.json();
      console.log("Added test detection:", testData);
      alert(
        `Added test detection: ${testData.speed} mph at ${testData.distance} ft`,
      );
    } catch (error) {
      console.error("Failed to add test data:", error);
      alert("Failed to add test data");
    }
  };

  return (
    <div className="camera-feed-container">
      <div className="camera-header">
        <h3>Raspberry Pi Infrared Camera Feed</h3>
        <div className="connection-controls">
          <button
            onClick={isConnected ? handleDisconnect : handleConnect}
            className={`connect-btn ${isConnected ? "connected" : ""}`}
          >
            {isConnected ? "Disconnect" : "Connect to Backend"}
          </button>
          <button onClick={addTestData} className="test-btn">
            Add Test Detection
          </button>
        </div>
      </div>

      <div className="camera-display">
        {isConnected ? (
          <img
            src={`${backendUrl}/api/camera/stream`}
            alt="Raspberry Pi Camera Feed"
            className="camera-stream"
            onError={() => {
              console.log("Camera stream error");
              setIsConnected(false);
            }}
          />
        ) : (
          <img
            src={placeholderImage}
            alt="Camera Placeholder"
            className="camera-placeholder"
          />
        )}
      </div>

      <div className="camera-status">
        <div className="status-info">
          <span
            className={`status-indicator ${isConnected ? "connected" : "disconnected"}`}
          >
            {isConnected ? "● Live" : "● Disconnected"}
          </span>
          {systemStatus && (
            <div className="system-info">
              <small>
                Camera: {systemStatus.camera_connected ? "✅" : "❌"} | Sensor:{" "}
                {systemStatus.sensor_connected ? "✅" : "❌"} | Detections:{" "}
                {systemStatus.total_detections}
              </small>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CameraFeed;
