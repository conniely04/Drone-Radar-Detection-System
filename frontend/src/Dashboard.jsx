import React, { useState, useEffect } from "react";
import CameraFeed from "./components/CameraFeed";
import ObjectDetectionLog from "./components/ObjectDetectionLog";
import "./Dashboard.css";

const Dashboard = () => {
  const [backendStatus, setBackendStatus] = useState(null);
  const [backendUrl] = useState("http://localhost:5001");
  const [connectionError, setConnectionError] = useState(null);

  // Check backend connection on mount
  useEffect(() => {
    checkBackendConnection();

    // Check connection periodically
    const interval = setInterval(checkBackendConnection, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkBackendConnection = async () => {
    try {
      const response = await fetch(`${backendUrl}/`);
      const data = await response.json();
      setBackendStatus(data);
      setConnectionError(null);
    } catch (error) {
      console.error("Backend connection error:", error);
      setConnectionError("Backend server is not running");
      setBackendStatus(null);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Object Detection Dashboard</h1>
        <p>Real-time monitoring system with Raspberry Pi infrared camera</p>

        {/* Backend Status Indicator */}
        <div className="backend-status">
          {connectionError ? (
            <div className="status-error">
              ⚠️ {connectionError} - Start backend with:{" "}
              <code>python backend/app.py</code>
            </div>
          ) : backendStatus ? (
            <div className="status-success">
              ✅ Backend connected - {backendStatus.message}
            </div>
          ) : (
            <div className="status-loading">
              🔄 Checking backend connection...
            </div>
          )}
        </div>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-grid">
          {/* Camera Feed Section */}
          <section className="camera-section">
            <CameraFeed />
          </section>

          {/* Detection Log Section */}
          <section className="log-section">
            <ObjectDetectionLog />
          </section>
        </div>
      </main>

      <footer className="dashboard-footer">
        <p>&copy; 2026 Senior Project - Object Detection System</p>
      </footer>
    </div>
  );
};

export default Dashboard;
