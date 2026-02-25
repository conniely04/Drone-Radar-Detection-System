from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import cv2
import json
import threading
import time
from datetime import datetime
import serial
import serial.tools.list_ports
import queue
import logging
from collections import deque

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ObjectDetectionSystem:
    def __init__(self):
        self.camera = None
        self.serial_connection = None
        self.detection_data = deque(maxlen=100)  # Store last 100 detections
        self.is_running = False
        self.data_queue = queue.Queue()
        
        # Camera settings
        self.camera_width = 640
        self.camera_height = 480
        self.camera_fps = 30
        
        # Serial settings for radar sensor
        self.serial_port = None
        self.baud_rate = 9600
        
    def initialize_camera(self):
        """Initialize the camera (Pi Camera or USB camera)"""
        try:
            # Try to initialize camera (0 for first camera, usually Pi camera)
            self.camera = cv2.VideoCapture(0)
            
            if not self.camera.isOpened():
                logger.error("Failed to open camera")
                return False
                
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.camera_fps)
            
            logger.info("Camera initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Camera initialization error: {e}")
            return False
    
    def initialize_serial(self, port=None):
        """Initialize serial connection for radar sensor"""
        try:
            if port is None:
                # Auto-detect serial ports
                ports = serial.tools.list_ports.comports()
                available_ports = [port.device for port in ports]
                logger.info(f"Available ports: {available_ports}")
                
                if available_ports:
                    port = available_ports[0]  # Use first available port
                else:
                    logger.warning("No serial ports found")
                    return False
            
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=self.baud_rate,
                timeout=1,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            self.serial_port = port
            logger.info(f"Serial connection established on {port}")
            return True
            
        except Exception as e:
            logger.error(f"Serial initialization error: {e}")
            return False
    
    def generate_camera_frames(self):
        """Generate camera frames for MJPEG streaming"""
        while self.is_running and self.camera:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    break
                
                # Add timestamp overlay
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, timestamp, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame, 
                                         [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
            except Exception as e:
                logger.error(f"Frame generation error: {e}")
                break
    
    def read_sensor_data(self):
        """Read data from radar sensor via serial"""
        while self.is_running and self.serial_connection:
            try:
                if self.serial_connection.in_waiting > 0:
                    # Read line from serial
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    
                    if line:
                        # Parse sensor data (adjust format based on your sensor)
                        # Expected format: "SPEED:45,DISTANCE:30,CONFIDENCE:0.95"
                        data = self.parse_sensor_data(line)
                        if data:
                            self.add_detection(data)
                
                time.sleep(0.1)  # Small delay to prevent CPU overload
                
            except Exception as e:
                logger.error(f"Sensor reading error: {e}")
                time.sleep(1)
    
    def parse_sensor_data(self, data_string):
        """Parse incoming sensor data string"""
        try:
            # Example parsing - adjust based on your radar sensor format
            parts = data_string.split(',')
            data = {}
            
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    key = key.strip().upper()
                    
                    if key == 'SPEED':
                        data['speed'] = float(value)
                    elif key == 'DISTANCE':
                        data['distance'] = float(value)
                    elif key == 'CONFIDENCE':
                        data['confidence'] = float(value)
            
            # Validate data
            if 'speed' in data and 'distance' in data:
                return {
                    'speed': data['speed'],
                    'distance': data['distance'],
                    'confidence': data.get('confidence', 0.9),
                    'object_type': 'Vehicle',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Data parsing error: {e}")
            
        return None
    
    def add_detection(self, detection_data):
        """Add new detection to the data store"""
        detection_data['id'] = int(time.time() * 1000)  # Use timestamp as ID
        self.detection_data.appendleft(detection_data)
        logger.info(f"New detection: Speed {detection_data['speed']} mph, "
                   f"Distance {detection_data['distance']} ft")
    
    def start_system(self):
        """Start the detection system"""
        self.is_running = True
        
        # Start camera
        if self.initialize_camera():
            logger.info("Camera system started")
        
        # Start serial communication
        if self.initialize_serial():
            # Start sensor reading thread
            sensor_thread = threading.Thread(target=self.read_sensor_data)
            sensor_thread.daemon = True
            sensor_thread.start()
            logger.info("Sensor system started")
    
    def stop_system(self):
        """Stop the detection system"""
        self.is_running = False
        
        if self.camera:
            self.camera.release()
            self.camera = None
            
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
            
        logger.info("Detection system stopped")

# Initialize the detection system
detection_system = ObjectDetectionSystem()

@app.route('/')
def index():
    """API status endpoint"""
    return jsonify({
        'status': 'running',
        'message': 'Object Detection Backend API',
        'camera_available': detection_system.camera is not None,
        'sensor_available': detection_system.serial_connection is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/camera/stream')
def camera_stream():
    """MJPEG camera stream endpoint"""
    if not detection_system.camera:
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
        'camera_connected': detection_system.camera is not None,
        'sensor_connected': detection_system.serial_connection is not None,
        'serial_port': detection_system.serial_port,
        'total_detections': len(detection_system.detection_data),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/system/start', methods=['POST'])
def start_system():
    """Start the detection system"""
    try:
        detection_system.start_system()
        return jsonify({'message': 'System started successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/stop', methods=['POST'])
def stop_system():
    """Stop the detection system"""
    try:
        detection_system.stop_system()
        return jsonify({'message': 'System stopped successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensor/test', methods=['POST'])
def test_sensor_data():
    """Add test detection data (for development)"""
    import random
    
    test_data = {
        'speed': round(random.uniform(25, 50), 1),
        'distance': round(random.uniform(20, 60), 1),
        'confidence': round(random.uniform(0.8, 0.99), 2),
        'object_type': 'Vehicle',
        'timestamp': datetime.now().isoformat()
    }
    
    detection_system.add_detection(test_data)
    return jsonify(test_data)

if __name__ == '__main__':
    # Start the detection system
    detection_system.start_system()
    
    try:
        # Run Flask app
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
    finally:
        # Clean up on exit
        detection_system.stop_system()