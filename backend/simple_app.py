from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import time
import random
import threading
from collections import deque

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Mock detection data storage
detection_data = deque(maxlen=100)

# Initialize with some test data
def initialize_test_data():
    test_detections = [
        {
            'id': 1,
            'speed': 35.2,
            'distance': 45.0,
            'object_type': 'Vehicle',
            'confidence': 0.92,
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 2,
            'speed': 28.7,
            'distance': 38.5,
            'object_type': 'Vehicle',
            'confidence': 0.88,
            'timestamp': datetime.now().isoformat()
        }
    ]
    for detection in test_detections:
        detection_data.appendleft(detection)

@app.route('/')
def index():
    """API status endpoint"""
    return jsonify({
        'status': 'running',
        'message': 'Object Detection Backend API',
        'camera_available': False,
        'sensor_available': False,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/detections')
def get_detections():
    """Get all detection data"""
    detections = list(detection_data)
    return jsonify({
        'detections': detections,
        'count': len(detections),
        'latest': detections[0] if detections else None
    })

@app.route('/api/detections/latest')
def get_latest_detection():
    """Get the most recent detection"""
    if detection_data:
        return jsonify(detection_data[0])
    else:
        return jsonify({'message': 'No detections available'}), 404

@app.route('/api/system/status')
def system_status():
    """Get system status"""
    return jsonify({
        'is_running': True,
        'camera_connected': False,
        'sensor_connected': False,
        'serial_port': None,
        'total_detections': len(detection_data),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/system/start', methods=['POST'])
def start_system():
    """Start the detection system"""
    return jsonify({'message': 'System started successfully'})

@app.route('/api/system/stop', methods=['POST'])
def stop_system():
    """Stop the detection system"""
    return jsonify({'message': 'System stopped successfully'})

@app.route('/api/sensor/test', methods=['POST'])
def test_sensor_data():
    """Add test detection data (for development)"""
    test_data = {
        'id': int(time.time() * 1000),
        'speed': round(random.uniform(25, 50), 1),
        'distance': round(random.uniform(20, 60), 1),
        'confidence': round(random.uniform(0.8, 0.99), 2),
        'object_type': 'Vehicle',
        'timestamp': datetime.now().isoformat()
    }
    
    detection_data.appendleft(test_data)
    print(f"Added test detection: Speed {test_data['speed']} mph, Distance {test_data['distance']} ft")
    return jsonify(test_data)

@app.route('/api/camera/stream')
def camera_stream():
    """Mock camera stream - returns 404 since no camera available"""
    return "Camera not available in demo mode", 404

if __name__ == '__main__':
    # Initialize test data
    initialize_test_data()
    
    print("Starting Object Detection Backend API (Demo Mode)")
    print("Features available:")
    print("- Detection data endpoints")
    print("- Test data generation")
    print("- System status")
    print("Camera streaming disabled (requires OpenCV)")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)