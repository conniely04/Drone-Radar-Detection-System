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
import os
import sys

# Import vision detection module
from video_source import read_frame, start_video, stop_video
from vision import VisionProcessor, detect_drone_in_frame
from detector import get_detector_status

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
        self.raw_sensor_data = deque(maxlen=1000)  # Store raw serial data
        self.camera_lock = threading.Lock()
        self.sensor_thread = None
        
        # Camera settings
        self.camera_width = 640
        self.camera_height = 480
        self.camera_fps = 30
        self.camera_device = 0
        self.vision_processor = VisionProcessor()
        
        # Serial settings for radar sensor
        self.serial_port = None
        self.baud_rate = 9600
        
    def initialize_camera(self):
        """Initialize the camera (Pi Camera or USB camera)"""
        with self.camera_lock:
            if self.camera:
                return True

            try:
                self.camera = start_video(
                    self.camera_device,
                    width=self.camera_width,
                    height=self.camera_height,
                    fps=self.camera_fps,
                )
                
                if not self.camera:
                    logger.error("Failed to open camera")
                    return False

                ret, frame = read_frame(self.camera)
                if not ret or frame is None:
                    logger.error("Camera opened but did not return a test frame")
                    stop_video(self.camera)
                    self.camera = None
                    return False
                
                logger.info("Camera initialized successfully")
                return True
                
            except Exception as e:
                logger.error(f"Camera initialization error: {e}")
                self.camera = None
                return False

    def start_camera(self):
        """Start the camera while keeping the backend system marked as running."""
        self.is_running = True
        if self.initialize_camera():
            logger.info("Camera system started")
            return True
        return False

    def stop_camera(self):
        """Stop only the camera and leave the rest of the backend running."""
        with self.camera_lock:
            if self.camera:
                stop_video(self.camera)
                self.camera = None

        self.vision_processor.latest = {
            "detections": [],
            "drone_detected": False,
            "count": 0,
            "timestamp": None,
        }
        logger.info("Camera system stopped")

    def retry_camera_start(self, attempts=5, delay_seconds=2.0):
        """Retry camera startup in the background for Pi boot timing races."""
        def _retry():
            for attempt in range(1, attempts + 1):
                if self.camera or not self.is_running:
                    return
                logger.info("Retrying camera startup (%s/%s)", attempt, attempts)
                if self.start_camera():
                    return
                time.sleep(delay_seconds)

        retry_thread = threading.Thread(target=_retry)
        retry_thread.daemon = True
        retry_thread.start()
    
    def initialize_serial(self, port=None):
        """Initialize serial connection for radar sensor"""
        try:
            # Close any existing connection first
            if self.serial_connection:
                try:
                    self.serial_connection.close()
                    logger.info("Closed existing serial connection")
                except:
                    pass
                self.serial_connection = None
            
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
            
            logger.info(f"Attempting to connect to {port}...")
            
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
            
        except PermissionError as e:
            error_msg = f"Permission denied for {port}. Try: sudo chmod 666 {port}"
            logger.error(f"Serial initialization error: {error_msg}")
            return False
        except serial.SerialException as e:
            error_msg = f"Serial port error: {str(e)}"
            logger.error(f"Serial initialization error: {error_msg}")
            return False
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Serial initialization error: {error_msg}")
            return False
    
    def generate_camera_frames(self):
        """Generate camera frames for MJPEG streaming"""
        while self.is_running and self.camera:
            try:
                ret, frame = read_frame(self.camera)
                if not ret:
                    break

                frame, _vision_events = self.vision_processor.process_frame(frame)
                
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

            time.sleep(1.0 / max(self.camera_fps, 1))
    
    def read_sensor_data(self):
        """Read data from radar sensor via serial"""
        while self.is_running and self.serial_connection:
            try:
                if self.serial_connection.in_waiting > 0:
                    # Read line from serial
                    try:
                        line = self.serial_connection.readline().decode('utf-8').strip()
                    except:
                        line = self.serial_connection.readline().decode('latin-1').strip()
                    
                    if line:
                        # Store raw data
                        raw_entry = {
                            'timestamp': datetime.now().isoformat(),
                            'raw_data': line
                        }
                        self.raw_sensor_data.appendleft(raw_entry)
                        logger.info(f"Raw sensor data: {line}")

                        # Parse sensor data (adjust format based on your sensor)
                        # Expected format: "SPEED:45,DISTANCE:30,CONFIDENCE:0.95" or JSON-like
                        data = self.parse_sensor_data(line)
                        if data:
                            # Attach raw line to the parsed detection so frontend can show it
                            data['raw_data'] = line
                            self.add_detection(data)
                
                time.sleep(0.05)  # Small delay to prevent CPU overload
                
            except Exception as e:
                logger.error(f"Sensor reading error: {e}")
                time.sleep(1)
    
    def parse_sensor_data(self, data_string):
        """Parse incoming sensor data string"""
        try:
            # Try to parse either JSON-like or comma-separated key:value pairs
            data = {}
            s = data_string.strip()
            # If it looks like JSON, try json.loads
            if (s.startswith('{') and s.endswith('}')) or (s.startswith('{"') and s.endswith('}')):
                try:
                    j = json.loads(s)
                    for k, v in j.items():
                        key = k.strip().upper()
                        if key == 'SPEED' or key == 'DETECTEDOBJECTVELOCITY' or key == 'VELOCITY':
                            try:
                                data['speed'] = float(v)
                            except:
                                pass
                        elif key == 'DISTANCE':
                            try:
                                data['distance'] = float(v)
                            except:
                                pass
                        elif key == 'MAGNITUDE':
                            try:
                                data['magnitude'] = float(v)
                            except:
                                pass
                        elif key == 'CONFIDENCE':
                            try:
                                data['confidence'] = float(v)
                            except:
                                pass
                        elif key == 'UNIT':
                            data['unit'] = str(v)
                        elif key == 'TIME':
                            try:
                                data['time'] = float(v)
                            except:
                                data['time'] = None
                except Exception as e:
                    logger.debug(f"JSON parsing error: {e}")
                    # fall back to key:value parsing below
                    pass

            if not data:
                parts = data_string.split(',')
                for part in parts:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        key = key.strip().upper()
                        value = value.strip().strip('"')

                        if key == 'SPEED' or key == 'DETECTEDOBJECTVELOCITY' or key == 'VELOCITY':
                            try:
                                data['speed'] = float(value)
                            except:
                                pass
                        elif key == 'DISTANCE':
                            try:
                                data['distance'] = float(value)
                            except:
                                pass
                        elif key == 'MAGNITUDE':
                            try:
                                data['magnitude'] = float(value)
                            except:
                                pass
                        elif key == 'CONFIDENCE':
                            try:
                                data['confidence'] = float(value)
                            except:
                                pass
                        elif key == 'UNIT':
                            data['unit'] = value
                        elif key == 'TIME':
                            try:
                                data['time'] = float(value)
                            except:
                                pass

            if not data:
                try:
                    data['speed'] = float(s)
                    data['unit'] = 'mps'
                except ValueError:
                    pass

            # Normalize: require at least a speed and time or speed alone
            if 'speed' in data:
                # default unit
                if 'unit' not in data:
                    data['unit'] = 'unknown'
                # attach metadata
                detection = {
                    'speed': data.get('speed'),
                    'distance': data.get('distance'),
                    'magnitude': data.get('magnitude'),
                    'confidence': data.get('confidence', None),
                    'unit': data.get('unit'),
                    'time': data.get('time', None),
                    'object_type': 'Vehicle',
                    'timestamp': datetime.now().isoformat()
                }
                return detection
            else:
                logger.debug(f"Ignoring unparsable sensor data: {data_string}")
                
        except Exception as e:
            logger.error(f"Data parsing error: {e}")
            
        return None
    
    def add_detection(self, detection_data):
        """Add new detection to the data store"""
        detection_data['id'] = int(time.time() * 1000)  # Use timestamp as ID

        # Compute distance/position using magnitude value if available, otherwise use velocity trapezoidal rule
        try:
            # If magnitude is available, use it directly for distance/position
            if detection_data.get('magnitude') is not None:
                # Use magnitude directly as distance in cm
                detection_data['computed_distance'] = detection_data.get('magnitude')
                detection_data['computed_distance_unit'] = 'cm'
                logger.info(f"Using magnitude for distance: {detection_data['computed_distance']} cm")
            else:
                # Fall back to velocity-based distance calculation using trapezoidal rule
                prev = self.detection_data[0] if len(self.detection_data) > 0 else None
                if prev and detection_data.get('time') is not None and prev.get('time') is not None and detection_data.get('speed') is not None and prev.get('speed') is not None:
                    delta_t = detection_data['time'] - prev['time']
                    if delta_t < 0:
                        delta_t = abs(delta_t)
                    # Use trapezoidal rule: distance = (v1 + v2) / 2 * delta_t
                    current_speed = abs(detection_data['speed'])
                    prev_speed = abs(prev['speed'])
                    v_avg = (current_speed + prev_speed) / 2.0
                    computed_distance = v_avg * delta_t
                    detection_data['computed_distance'] = computed_distance
                    detection_data['computed_distance_unit'] = detection_data.get('unit')
                    logger.debug(f"Using velocity trapezoidal rule: {computed_distance}")
                else:
                    detection_data['computed_distance'] = detection_data.get('distance')
                    detection_data['computed_distance_unit'] = detection_data.get('unit')
                    logger.debug(f"Using fallback distance: {detection_data['computed_distance']}")
        except Exception as e:
            logger.error(f"Distance compute error: {e}", exc_info=True)

        self.detection_data.appendleft(detection_data)
        logger.info(f"New detection: Speed {detection_data.get('speed')} {detection_data.get('unit')}, "
                   f"Computed distance {detection_data.get('computed_distance')}{detection_data.get('computed_distance_unit')}")

    def add_vision_detection(self, detection_data):
        """Add a confirmed computer-vision drone detection to the shared detection store."""
        detection_data['id'] = int(time.time() * 1000)
        self.detection_data.appendleft(detection_data)
        logger.info(
            "Vision detection: track_id=%s speed=%.2f %s bbox=%s",
            detection_data.get('track_id'),
            detection_data.get('speed') or 0,
            detection_data.get('unit'),
            detection_data.get('bbox'),
        )
    
    def start_system(self):
        """Start the detection system"""
        self.is_running = True
        
        # Start camera
        if not self.start_camera():
            self.retry_camera_start()
        
        # Start serial communication
        if self.serial_connection or self.initialize_serial():
            if not self.sensor_thread or not self.sensor_thread.is_alive():
                self.sensor_thread = threading.Thread(target=self.read_sensor_data)
                self.sensor_thread.daemon = True
                self.sensor_thread.start()
                logger.info("Sensor system started")

    def run_init_sequence(self):
        """Send initialization command sequence to the serial device and collect immediate responses"""
        if not self.serial_connection:
            logger.error("Cannot run init sequence: serial not connected")
            return

        def _run():
            try:
                # initial wait
                time.sleep(0.5)
                cmds = ['OJ', 'IG', 'ON', 'OU', 'OS', 'SV', 'C=1771982622:', 'OM']
                for cmd in cmds:
                    try:
                        to_send = (cmd + '\n').encode('utf-8')
                        self.serial_connection.write(to_send)
                        logger.info(f"Sent init cmd: {cmd}")
                        time.sleep(0.1)
                    except Exception as e:
                        logger.error(f"Error sending cmd {cmd}: {e}")

                # read for a short window to capture immediate responses
                end_t = time.time() + 1.5
                while time.time() < end_t:
                    try:
                        if self.serial_connection.in_waiting > 0:
                            try:
                                line = self.serial_connection.readline().decode('utf-8').strip()
                            except:
                                line = self.serial_connection.readline().decode('latin-1').strip()
                            if line:
                                raw_entry = {'timestamp': datetime.now().isoformat(), 'raw_data': line}
                                self.raw_sensor_data.appendleft(raw_entry)
                                logger.info(f"Init response: {line}")
                                # try to parse and add detection
                                data = self.parse_sensor_data(line)
                                if data:
                                    data['raw_data'] = line
                                    self.add_detection(data)
                    except Exception as e:
                        logger.error(f"Error reading init responses: {e}")
                        break
                    time.sleep(0.05)
            except Exception as e:
                logger.error(f"Init sequence error: {e}")

        t = threading.Thread(target=_run)
        t.daemon = True
        t.start()
    
    def stop_system(self):
        """Stop the detection system"""
        self.is_running = False
        
        self.stop_camera()
            
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
        self.sensor_thread = None
            
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
        detection_system.start_camera()
    if not detection_system.camera:
        return "Camera not available", 503
    
    return Response(
        detection_system.generate_camera_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/api/camera/start', methods=['POST'])
def start_camera():
    """Start only the camera stream without changing the radar serial connection."""
    try:
        if detection_system.start_camera():
            return jsonify({'message': 'Camera started successfully'})
        return jsonify({'error': 'Camera not available'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    """Stop only the camera stream and leave radar serial connection alone."""
    try:
        detection_system.stop_camera()
        return jsonify({'message': 'Camera stopped successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    latest_vision = detection_system.vision_processor.latest
    return jsonify({
        'is_running': detection_system.is_running,
        'camera_connected': detection_system.camera is not None,
        'sensor_connected': detection_system.serial_connection is not None,
        'serial_port': detection_system.serial_port,
        'total_detections': len(detection_system.detection_data),
        'vision': latest_vision,
        'detector': get_detector_status(),
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

# Removed test sensor endpoint to prevent insertion of fake data

@app.route('/api/sensor/raw')
def get_raw_sensor_data():
    """Get raw serial sensor data (most recent readings)"""
    raw_data = list(detection_system.raw_sensor_data)
    return jsonify({
        'raw_data': raw_data,
        'count': len(raw_data),
        'latest': raw_data[0] if raw_data else None
    })

@app.route('/api/sensor/stream')
def sensor_stream():
    """Stream raw sensor data to frontend via Server-Sent Events"""
    def generate():
        last_count = 0
        while detection_system.is_running:
            try:
                current_count = len(detection_system.raw_sensor_data)
                if current_count > last_count:
                    # New data available
                    raw_data = list(detection_system.raw_sensor_data)
                    new_items = raw_data[:current_count - last_count]
                    for item in reversed(new_items):  # Reverse to get chronological order
                        yield f"data: {json.dumps(item)}\n\n"
                    last_count = current_count
                
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Stream error: {e}")
                break
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/system/port-info', methods=['POST'])
def set_serial_port():
    """Set the serial port to use"""
    try:
        data = request.json
        port = data.get('port')
        
        if not port:
            return jsonify({'error': 'Port not specified'}), 400
        
        logger.info(f"Attempting to connect to port: {port}")
        
        # Stop existing connection
        if detection_system.is_running:
            logger.info("Stopping existing system...")
            detection_system.stop_system()
        
        # Try to initialize with new port
        if detection_system.initialize_serial(port):
            detection_system.is_running = True
            # Start sensor reading thread
            sensor_thread = threading.Thread(target=detection_system.read_sensor_data)
            sensor_thread.daemon = True
            sensor_thread.start()
            # Run initialization command sequence in background
            try:
                detection_system.run_init_sequence()
            except Exception as e:
                logger.error(f"Failed to run init sequence: {e}")
            
            logger.info(f"Successfully connected to {port}")
            return jsonify({
                'message': f'Serial port {port} connected',
                'port': port,
                'status': 'connected'
            })
        else:
            error_msg = f"Failed to connect to {port}. Check if port is in use or try: sudo chmod 666 {port}"
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 500
            
    except Exception as e:
        error_msg = f"Connection error: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/api/system/available-ports')
def get_available_ports():
    """Get list of available serial ports"""
    try:
        ports = serial.tools.list_ports.comports()
        available_ports = [
            {
                'device': port.device,
                'description': port.description,
                'manufacturer': port.manufacturer
            }
            for port in ports
        ]
        return jsonify({'ports': available_ports})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vision/detect-drone', methods=['POST'])
def detect_drone():
    """Detect drones in uploaded image"""
    try:
        data = request.json
        image_base64 = data.get('image')
        
        if not image_base64:
            return jsonify({'error': 'No image provided'}), 400
        
        # Call the detection function from vision module
        result = detect_drone_in_frame(image_base64)
        
        return jsonify({
            'detections': result.get('detections', []),
            'drone_detected': result.get('drone_detected', False),
            'count': result.get('count', 0),
            'error': result.get('error'),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Drone detection endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Start the detection system
    detection_system.start_system()
    
    try:
        # Run Flask app
        debug = os.environ.get('DEBUG', 'False').lower() == 'true'
        port = int(os.environ.get('PORT', 5001))
        app.run(host='0.0.0.0', port=port, debug=debug, threaded=True, use_reloader=False)
    finally:
        # Clean up on exit
        detection_system.stop_system()
