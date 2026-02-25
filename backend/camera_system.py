import cv2
import threading
import time
import logging
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class CameraSystem:
    """Handle camera operations for Raspberry Pi"""
    
    def __init__(self, camera_id=0, width=640, height=480, fps=30):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        self.camera = None
        self.is_streaming = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Try to detect if we're on Raspberry Pi
        self.is_raspberry_pi = self._detect_raspberry_pi()
        
    def _detect_raspberry_pi(self):
        """Detect if running on Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                return 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo
        except:
            return False
    
    def initialize(self):
        """Initialize the camera"""
        try:
            # Initialize camera
            self.camera = cv2.VideoCapture(self.camera_id)
            
            if not self.camera.isOpened():
                logger.error(f"Failed to open camera {self.camera_id}")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            # For Raspberry Pi, try to set additional properties
            if self.is_raspberry_pi:
                # Set buffer size to reduce latency
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # Try to enable auto-exposure for better infrared performance
                self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            
            # Test frame capture
            ret, frame = self.camera.read()
            if not ret:
                logger.error("Failed to capture test frame")
                return False
            
            logger.info(f"Camera initialized: {self.width}x{self.height} @ {self.fps}fps")
            logger.info(f"Raspberry Pi detected: {self.is_raspberry_pi}")
            
            return True
            
        except Exception as e:
            logger.error(f"Camera initialization error: {e}")
            return False
    
    def start_streaming(self):
        """Start camera streaming in a separate thread"""
        if not self.camera:
            logger.error("Camera not initialized")
            return False
        
        self.is_streaming = True
        stream_thread = threading.Thread(target=self._streaming_loop)
        stream_thread.daemon = True
        stream_thread.start()
        
        logger.info("Camera streaming started")
        return True
    
    def stop_streaming(self):
        """Stop camera streaming"""
        self.is_streaming = False
        logger.info("Camera streaming stopped")
    
    def _streaming_loop(self):
        """Main streaming loop"""
        while self.is_streaming and self.camera:
            try:
                ret, frame = self.camera.read()
                if ret:
                    # Process frame (add overlays, etc.)
                    processed_frame = self._process_frame(frame)
                    
                    # Update current frame thread-safely
                    with self.frame_lock:
                        self.current_frame = processed_frame
                else:
                    logger.warning("Failed to capture frame")
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                time.sleep(0.1)
    
    def _process_frame(self, frame):
        """Process frame (add overlays, filters, etc.)"""
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add system info
        info_text = f"Resolution: {frame.shape[1]}x{frame.shape[0]}"
        cv2.putText(frame, info_text, (10, frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # If infrared camera, you might want to apply specific processing
        if self.is_raspberry_pi:
            # Example: Enhance contrast for infrared
            frame = self._enhance_infrared(frame)
        
        return frame
    
    def _enhance_infrared(self, frame):
        """Enhance infrared camera image"""
        try:
            # Convert to grayscale for infrared processing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply histogram equalization to improve contrast
            enhanced = cv2.equalizeHist(gray)
            
            # Convert back to BGR for streaming
            frame = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
        except Exception as e:
            logger.error(f"Infrared enhancement error: {e}")
        
        return frame
    
    def get_frame(self):
        """Get current frame (thread-safe)"""
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None
    
    def generate_mjpeg_frames(self):
        """Generate MJPEG frames for HTTP streaming"""
        while self.is_streaming:
            frame = self.get_frame()
            if frame is not None:
                try:
                    # Encode frame as JPEG
                    ret, buffer = cv2.imencode('.jpg', frame, 
                                             [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + 
                               frame_bytes + b'\r\n')
                except Exception as e:
                    logger.error(f"Frame encoding error: {e}")
            
            time.sleep(1.0 / self.fps)  # Control frame rate
    
    def capture_snapshot(self):
        """Capture a single snapshot"""
        frame = self.get_frame()
        if frame is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snapshot_{timestamp}.jpg"
            cv2.imwrite(filename, frame)
            logger.info(f"Snapshot saved: {filename}")
            return filename
        return None
    
    def get_camera_info(self):
        """Get camera information"""
        if not self.camera:
            return None
        
        return {
            'width': int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.camera.get(cv2.CAP_PROP_FPS)),
            'backend': self.camera.getBackendName(),
            'is_raspberry_pi': self.is_raspberry_pi,
            'is_streaming': self.is_streaming
        }
    
    def release(self):
        """Release camera resources"""
        self.stop_streaming()
        if self.camera:
            self.camera.release()
            self.camera = None
            logger.info("Camera released")

# Raspberry Pi specific camera using picamera2 (alternative implementation)
try:
    from picamera2 import Picamera2
    from picamera2.encoders import MJPEGEncoder
    from picamera2.outputs import FileOutput
    import io
    
    class RaspberryPiCamera:
        """Alternative camera implementation using picamera2"""
        
        def __init__(self, width=640, height=480, fps=30):
            self.width = width
            self.height = height
            self.fps = fps
            self.picam2 = None
            self.is_streaming = False
        
        def initialize(self):
            """Initialize Pi Camera using picamera2"""
            try:
                self.picam2 = Picamera2()
                
                # Configure camera
                config = self.picam2.create_video_configuration(
                    main={"size": (self.width, self.height)}
                )
                self.picam2.configure(config)
                
                self.picam2.start()
                logger.info("Raspberry Pi camera initialized with picamera2")
                return True
                
            except Exception as e:
                logger.error(f"picamera2 initialization error: {e}")
                return False
        
        def generate_mjpeg_frames(self):
            """Generate MJPEG frames using picamera2"""
            while self.is_streaming and self.picam2:
                try:
                    # Capture frame
                    frame = self.picam2.capture_array()
                    
                    # Add timestamp
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, timestamp, (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    # Encode as JPEG
                    ret, buffer = cv2.imencode('.jpg', frame, 
                                             [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + 
                               frame_bytes + b'\r\n')
                    
                    time.sleep(1.0 / self.fps)
                    
                except Exception as e:
                    logger.error(f"picamera2 frame error: {e}")
                    break
        
        def start_streaming(self):
            self.is_streaming = True
            return True
        
        def stop_streaming(self):
            self.is_streaming = False
        
        def release(self):
            if self.picam2:
                self.picam2.stop()
                self.picam2 = None

except ImportError:
    logger.info("picamera2 not available, using OpenCV camera")
    RaspberryPiCamera = None