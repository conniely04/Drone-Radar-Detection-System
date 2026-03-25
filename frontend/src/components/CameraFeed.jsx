import React, { useState, useEffect, useRef } from "react";
import "./CameraFeed.css";

const CameraFeed = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [backendUrl] = useState("http://localhost:5001");
  const [droneDetected, setDroneDetected] = useState(false);
  const [droneDetectionRunning, setDroneDetectionRunning] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const canvasRef = useRef(null);
  const detectionIntervalRef = useRef(null);

  // Placeholder for when camera is not connected
  const placeholderImage =
    "data:image/svg+xml,%3Csvg width='640' height='480' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='100%25' height='100%25' fill='%23333'/%3E%3Ctext x='50%25' y='50%25' font-size='20' fill='white' text-anchor='middle' dy='.3em'%3EMac Laptop Camera Feed%3C/text%3E%3C/svg%3E";

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (detectionIntervalRef.current) {
        clearInterval(detectionIntervalRef.current);
      }
    };
  }, []);

  // Check system status on component mount
  useEffect(() => {
    checkSystemStatus();
  }, []);

  // Start drone detection when camera connects
  useEffect(() => {
    if (isConnected && !droneDetectionRunning) {
      startDroneDetection();
    } else if (!isConnected && droneDetectionRunning) {
      stopDroneDetection();
    }
  }, [isConnected]);

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
      // Request access to camera
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });

      console.log("Camera stream obtained:", stream);
      streamRef.current = stream;

      // Set the video element to display the stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        console.log("Stream attached to video element");
      }

      setIsConnected(true);
      await checkSystemStatus();
    } catch (error) {
      console.error("Failed to access camera:", error);
      alert("Failed to access camera. Please check permissions and try again.");
    }
  };

  const startDroneDetection = () => {
    setDroneDetectionRunning(true);

    // Run drone detection every 2 seconds
    detectionIntervalRef.current = setInterval(async () => {
      if (
        videoRef.current &&
        videoRef.current.readyState === videoRef.current.HAVE_ENOUGH_DATA
      ) {
        const imageBase64 = captureFrameAsBase64();
        if (imageBase64) {
          try {
            const response = await fetch(
              `${backendUrl}/api/vision/detect-drone`,
              {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image: imageBase64 }),
              },
            );

            const result = await response.json();
            setDroneDetected(result.drone_detected);

            if (result.drone_detected) {
              console.log("🚁 Drone detected!", result);
            }
          } catch (error) {
            console.error("Drone detection error:", error);
          }
        }
      }
    }, 2000);
  };

  const stopDroneDetection = () => {
    setDroneDetectionRunning(false);
    if (detectionIntervalRef.current) {
      clearInterval(detectionIntervalRef.current);
      detectionIntervalRef.current = null;
    }
    setDroneDetected(false);
  };

  const captureFrameAsBase64 = () => {
    try {
      if (!canvasRef.current || !videoRef.current) return null;

      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      const video = videoRef.current;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      ctx.drawImage(video, 0, 0);
      return canvas.toDataURL("image/jpeg").split(",")[1]; // Remove data URL prefix
    } catch (error) {
      console.error("Frame capture error:", error);
      return null;
    }
  };

  const handleDisconnect = () => {
    // Stop the camera stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsConnected(false);
  };

  return (
    <div className="camera-feed-container">
      <div className="camera-header">
        <h3>Mac Laptop Camera Feed</h3>
        <div className="connection-controls">
          <button
            onClick={isConnected ? handleDisconnect : handleConnect}
            className={`connect-btn ${isConnected ? "connected" : ""}`}
          >
            {isConnected ? "Disconnect Camera" : "Connect Camera"}
          </button>
        </div>
      </div>

      <div className="camera-display">
        {isConnected ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="camera-stream"
          />
        ) : (
          <img
            src={placeholderImage}
            alt="Camera Placeholder"
            className="camera-placeholder"
          />
        )}
        {/* Hidden canvas for frame capture */}
        <canvas ref={canvasRef} style={{ display: "none" }} />

        {/* Drone detection indicator */}
        {droneDetected && <div className="drone-alert">🚁 DRONE DETECTED</div>}
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
                Camera:{" "}
                {isConnected || systemStatus.camera_connected ? "✅" : "❌"} |
                Sensor: {systemStatus.sensor_connected ? "✅" : "❌"} |
                Detections: {systemStatus.total_detections}
              </small>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CameraFeed;
