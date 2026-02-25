from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import json
import threading
import time
from datetime import datetime
import logging
from collections import deque
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockDetectionSystem:
    """Mock detection system for development/testing"""
    
    def __init__(self):
        self.detection_data = deque(maxlen=100)
        self.is_running = False
        self.mock_camera_active = False
        self.mock_sensor_active = False
        
        # Add some initial mock data
        self._add_initial_data()
        
    def _add_initial_data(self):
        """Add some initial mock detection data"""
        base_time = datetime.now()
        mock_detections = [
            {
                'id': int(time.time() * 1000) - 300000,
                'speed': 35.2,
                'distance': 45,
                'confidence': 0.92,
                'object_type': 'Vehicle',
                'timestamp': (base_time.replace(minute=base_time.minute-5)).isoformat()
            },
            {
                'id': int(time.time() * 1000) - 240000,
                'speed': 28.7,
                'distance': 38,
                'confidence': 0.88,
                'object_type': 'Vehicle',
                'timestamp': (base_time.replace(minute=base_time.minute-4)).isoformat()
            },
            {
                'id': int(time.time() * 1000) - 180000,
                'speed': 42.1,
                'distance': 52,
                'confidence': 0.95,
                'object_type': 'Vehicle',
                'timestamp': (base_time.replace(minute=base_time.minute-3)).isoformat()
            }
        ]
        
        for detection in mock_detections:
            self.detection_data.append(detection)
    
    def generate_mock_frame(self):
        """Generate a mock camera frame (SVG placeholder)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="640" height="480" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#1a1a1a"/>
            <stop offset="100%" style="stop-color:#333333"/>
        </linearGradient>
    </defs>
    <rect width="100%" height="100%" fill="url(#bg)"/>
    
    <!-- Mock infrared objects -->
    <circle cx="320" cy="200" r="30" fill="#ff6b6b" opacity="0.8"/>
    <circle cx="180" cy="320" r="20" fill="#feca57" opacity="0.6"/>
    <circle cx="450" cy="150" r="25" fill="#48dbfb" opacity="0.7"/>
    
    <!-- Grid overlay -->
    <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#444" stroke-width="1" opacity="0.3"/>
        </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#grid)"/>
    
    <!-- Text overlays -->
    <text x="10" y="30" fill="white" font-family="monospace" font-size="14">{timestamp}</text>
    <text x="10" y="460" fill="white" font-family="monospace" font-size="12">Mock Infrared Camera - 640x480</text>
    <text x="320" y="250" fill="white" font-family="monospace" font-size="10" text-anchor="middle">Target: 35 mph</text>
    
    <!-- Crosshair -->
    <line x1="320" y1="230" x2="320" y2="250" stroke="red" stroke-width="2"/>
    <line x1="310" y1="240" x2="330" y2="240" stroke="red" stroke-width="2"/>
</svg>'''
        
        return svg_content.encode('utf-8')
    
    def generate_camera_frames(self):
        """Generate mock camera MJPEG frames"""
        while self.is_running and self.mock_camera_active:
            try:
                frame_data = self.generate_mock_frame()
                yield (b'--frame\r\n'
                       b'Content-Type: image/svg+xml\r\n\r\n' + frame_data + b'\r\n')
                time.sleep(1.0 / 10)  # 10 FPS for mock
            except Exception as e:
                logger.error(f"Mock frame generation error: {e}")
                break
    
    def generate_mock_detection(self):
        """Generate a random mock detection"""
        speeds = [25.3, 30.7, 35.2, 42.8, 38.1, 45.6, 28.9, 33.4, 40.2, 37.5]
        distances = [20.5, 25.8, 30.2, 35.7, 40.1, 45.3, 50.9, 55.2, 60.8, 65.4]
        confidences = [0.85, 0.89, 0.92, 0.87, 0.94, 0.91, 0.88, 0.96, 0.83, 0.90]
        
        return {
            'id': int(time.time() * 1000),
            'speed': random.choice(speeds),
            'distance': random.choice(distances),
            'confidence': random.choice(confidences),
            'object_type': 'Vehicle',
            'timestamp': datetime.now().isoformat()
        }
    
    def add_detection(self, detection_data):
        """Add new detection to the data store"""
        self.detection_data.appendleft(detection_data)
        logger.info(f"New detection: Speed {detection_data['speed']} mph, "
                   f"Distance {detection_data['distance']} ft")
    
    def mock_sensor_loop(self):
        """Mock sensor data generation loop"""
        while self.is_running and self.mock_sensor_active:
            try:
                # Generate detection every 8-15 seconds
                time.sleep(random.uniform(8, 15))
                
                if self.is_running and self.mock_sensor_active:
                    detection = self.generate_mock_detection()
                    self.add_detection(detection)
                    
            except Exception as e:
                logger.error(f"Mock sensor error: {e}")
    
    def start_system(self):
        """Start the mock detection system"""
        self.is_running = True
        self.mock_camera_active = True
        self.mock_sensor_active = True
        
        # Start mock sensor thread
        sensor_thread = threading.Thread(target=self.mock_sensor_loop)
        sensor_thread.daemon = True
        sensor_thread.start()
        
        logger.info("Mock detection system started")
    
    def stop_system(self):
        """Stop the mock detection system"""
        self.is_running = False
        self.mock_camera_active = False
        self.mock_sensor_active = False
        logger.info("Mock detection system stopped")

# Initialize the mock detection system
detection_system = MockDetectionSystem()

@app.route('/')
def index():
    """API status endpoint"""
    return jsonify({
        'status': 'running',
        'message': 'Object Detection Backend API (Development Mode)',
        'mode': 'development',
        'camera_available': detection_system.mock_camera_active,
        'sensor_available': detection_system.mock_sensor_active,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/camera/stream')
def camera_stream():
    """Mock MJPEG camera stream endpoint"""
    if not detection_system.mock_camera_active:
        return "Camera not available", 404
    
    return Response(
        detection_system.generate_camera_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/api/detections')
def get_detections():
    """Get all detection data"""
    detections = list(detection_system.detection_data)
    return jsonify({
        'detections': detections,
        'count': len(detections),
        'latest': detections[0] if detections else None
    })

@app.route('/api/detections/latest')
def get_latest_detection():
    """Get the most recent detection"""
    if detection_system.detection_data:
        return jsonify(detection_system.detection_data[0])
    else:
        return jsonify({'message': 'No detections available'}), 404

@app.route('/api/system/status')
def system_status():
    """Get system status"""
    return jsonify({
        'is_running': detection_system.is_running,
        'camera_connected': detection_system.mock_camera_active,
        'sensor_connected': detection_system.mock_sensor_active,
        'mode': 'development',
        'serial_port': 'mock',
        'total_detections': len(detection_system.detection_data),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/system/start', methods=['POST'])
def start_system():
    """Start the detection system"""
    try:
        detection_system.start_system()
        return jsonify({'message': 'Mock system started successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/stop', methods=['POST'])
def stop_system():
    """Stop the detection system"""
    try:
        detection_system.stop_system()
        return jsonify({'message': 'Mock system stopped successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensor/test', methods=['POST'])
def test_sensor_data():
    """Add test detection data"""
    test_data = detection_system.generate_mock_detection()
    detection_system.add_detection(test_data)
    return jsonify(test_data)

@app.route('/api/camera/snapshot', methods=['POST'])
def capture_snapshot():
    """Capture a snapshot (mock)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return jsonify({
        'filename': f'mock_snapshot_{timestamp}.svg',
        'timestamp': datetime.now().isoformat(),
        'message': 'Mock snapshot captured'
    })

if __name__ == '__main__':
    # Start the mock detection system
    detection_system.start_system()
    
    try:
        # Run Flask app on port 5001 to avoid conflicts
        app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
    finally:
        # Clean up on exit
        detection_system.stop_system()