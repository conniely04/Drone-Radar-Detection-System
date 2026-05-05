import React, { useState, useEffect } from "react";
import CameraFeed from "./components/CameraFeed";
import ObjectDetectionLog from "./components/ObjectDetectionLog";
import { backendUrl } from "./apiConfig";
import "./Dashboard.css";

const Dashboard = () => {
  const [backendStatus, setBackendStatus] = useState(null);
  const [connectionError, setConnectionError] = useState(null);
  const [availablePorts, setAvailablePorts] = useState([]);
  const [selectedPort, setSelectedPort] = useState("");

  // Check backend connection on mount
  useEffect(() => {
    checkBackendConnection();
    fetchAvailablePorts();

    // Check connection periodically
    const interval = setInterval(checkBackendConnection, 10000);
    return () => clearInterval(interval);
  }, []);

  // (Raw sensor panel removed) -- raw data still collected by backend but not shown here

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

  const fetchAvailablePorts = async () => {
    try {
      const response = await fetch(
        `${backendUrl}/api/system/available-ports`,
      );
      const data = await response.json();
      setAvailablePorts(data.ports || []);
    } catch (error) {
      console.error("Error fetching available ports:", error);
    }
  };

  const handleConnectPort = async () => {
    if (!selectedPort) {
      alert("Please select a port");
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/api/system/port-info`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ port: selectedPort }),
      });
      const data = await response.json();
      if (response.ok) {
        alert(`✅ Connected to ${selectedPort}`);
        checkBackendConnection();
      } else {
        console.error("Connection failed:", data);
        alert(
          `❌ Connection Failed:\n\n${data.error}\n\nTroubleshooting:\n1. Make sure the device is plugged in\n2. Try disconnecting and reconnecting the USB\n3. On macOS, you may need to run: sudo chmod 666 ${selectedPort}\n4. Close any other apps using this port (e.g., screen, minicom)`,
        );
      }
    } catch (error) {
      console.error("Connection error:", error);
      alert(`❌ Connection Error: ${error.message}`);
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
              ✅{" "}
              {backendStatus.sensor_connected
                ? "Serial port connected successfully"
                : backendStatus.camera_available
                  ? "Camera stream is online"
                  : "Backend is online"}
            </div>
          ) : (
            <div className="status-loading">
              🔄 Checking backend connection...
            </div>
          )}
        </div>

        {backendStatus && (
          <div className="serial-port-selector">
            <h3>Serial Port Configuration</h3>
            <div className="port-controls">
              <select
                value={selectedPort}
                onChange={(e) => setSelectedPort(e.target.value)}
                disabled={availablePorts.length === 0}
              >
                <option value="">Select a port...</option>
                {availablePorts.map((port) => (
                  <option key={port.device} value={port.device}>
                    {port.device} - {port.description}
                  </option>
                ))}
              </select>
              <button onClick={handleConnectPort} disabled={!selectedPort}>
                Connect Radar
              </button>
              <button onClick={fetchAvailablePorts}>Refresh Ports</button>
            </div>
            {backendStatus.sensor_connected && (
              <p className="port-connected">
                ✅ Connected to: {backendStatus.serial_port}
              </p>
            )}
          </div>
        )}
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

        {/* Raw sensor panel removed per user request */}
      </main>

      <footer className="dashboard-footer">
        <p>&copy; 2026 Senior Project - Object Detection System</p>
      </footer>
    </div>
  );
};

export default Dashboard;
