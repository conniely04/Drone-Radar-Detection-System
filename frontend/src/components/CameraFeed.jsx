import React, { useEffect, useMemo, useRef, useState } from "react";
import { backendUrl } from "../apiConfig";
import "./CameraFeed.css";

const CameraFeed = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [streamOnline, setStreamOnline] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [streamError, setStreamError] = useState(null);
  const autoStartAttemptedRef = useRef(false);

  const streamUrl = useMemo(
    () => `${backendUrl}/api/camera/stream?ts=${Date.now()}`,
    [streamOnline],
  );

  useEffect(() => {
    checkSystemStatus();
    const interval = setInterval(checkSystemStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (
      systemStatus?.is_running &&
      !systemStatus.camera_connected &&
      !isStarting &&
      !autoStartAttemptedRef.current
    ) {
      autoStartAttemptedRef.current = true;
      startBackendSystem();
    }
  }, [systemStatus, isStarting]);

  const checkSystemStatus = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/system/status`);
      const status = await response.json();
      setSystemStatus(status);
      setStreamOnline(Boolean(status.camera_connected));
    } catch (error) {
      console.error("Failed to check system status:", error);
      setSystemStatus(null);
      setStreamOnline(false);
    }
  };

  const startBackendSystem = async () => {
    setIsStarting(true);
    setStreamError(null);

    try {
      const response = await fetch(`${backendUrl}/api/camera/start`, {
        method: "POST",
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.error || "Backend could not start the camera");
      }
      await checkSystemStatus();
    } catch (error) {
      console.error("Camera start error:", error);
      setStreamError(error.message);
    } finally {
      setIsStarting(false);
    }
  };

  const stopBackendSystem = async () => {
    setStreamError(null);
    try {
      await fetch(`${backendUrl}/api/camera/stop`, { method: "POST" });
      await checkSystemStatus();
    } catch (error) {
      console.error("Camera stop error:", error);
      setStreamError(error.message);
    }
  };

  const vision = systemStatus?.vision;
  const droneDetected = Boolean(vision?.drone_detected);

  return (
    <div className="camera-feed-container">
      <div className="camera-header">
        <h3>Raspberry Pi Camera Feed</h3>
        <div className="connection-controls">
          <button
            onClick={streamOnline ? stopBackendSystem : startBackendSystem}
            className={`connect-btn ${streamOnline ? "connected" : ""}`}
            disabled={isStarting}
          >
            {streamOnline
              ? "Stop Camera"
              : isStarting
                ? "Starting..."
                : "Start Camera"}
          </button>
        </div>
      </div>

      <div className="camera-display">
        {streamOnline ? (
          <img
            src={streamUrl}
            alt="Live Raspberry Pi camera stream"
            className="camera-stream"
            onError={() => setStreamError("Camera stream is unavailable")}
            onLoad={() => setStreamError(null)}
          />
        ) : (
          <div className="camera-placeholder">
            <span>Camera stream offline</span>
          </div>
        )}

        {droneDetected && <div className="drone-alert">DRONE DETECTED</div>}
      </div>

      <div className="camera-status">
        <div className="status-info">
          <span
            className={`status-indicator ${streamOnline ? "connected" : "disconnected"}`}
          >
            {streamOnline ? "Live" : "Disconnected"}
          </span>
          {streamError && <small className="stream-error">{streamError}</small>}
          {systemStatus && (
            <div className="system-info">
              <small>
                Camera: {systemStatus.camera_connected ? "online" : "offline"} |
                Sensor: {systemStatus.sensor_connected ? "online" : "offline"} |
                Detections: {systemStatus.total_detections} | Vision boxes:{" "}
                {vision?.count || 0}
              </small>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CameraFeed;
