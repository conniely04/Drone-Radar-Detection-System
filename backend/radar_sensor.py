import serial
import serial.tools.list_ports
import threading
import time
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class RadarSensor:
    """Handle radar sensor communication via UART/Serial"""
    
    def __init__(self, port=None, baud_rate=9600, timeout=1.0):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.connection = None
        self.is_running = False
        self.data_callback = None
        
    def list_available_ports(self):
        """List all available serial ports"""
        ports = serial.tools.list_ports.comports()
        return [{'device': port.device, 'description': port.description} 
                for port in ports]
    
    def connect(self, port=None):
        """Connect to the radar sensor"""
        try:
            if port:
                self.port = port
            elif not self.port:
                # Auto-detect first available port
                available_ports = self.list_available_ports()
                if available_ports:
                    self.port = available_ports[0]['device']
                    logger.info(f"Auto-selected port: {self.port}")
                else:
                    logger.error("No serial ports available")
                    return False
            
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            # Test connection
            if self.connection.is_open:
                logger.info(f"Connected to radar sensor on {self.port}")
                return True
            else:
                logger.error(f"Failed to open connection to {self.port}")
                return False
                
        except Exception as e:
            logger.error(f"Sensor connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the radar sensor"""
        self.is_running = False
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info("Radar sensor disconnected")
    
    def set_data_callback(self, callback):
        """Set callback function for receiving parsed data"""
        self.data_callback = callback
    
    def parse_data(self, raw_data):
        """Parse raw sensor data - customize based on your radar sensor format"""
        try:
            # Remove any whitespace
            data_string = raw_data.strip()
            
            # Example parsing for different possible formats:
            
            # Format 1: JSON-like data
            if data_string.startswith('{') and data_string.endswith('}'):
                return json.loads(data_string)
            
            # Format 2: Comma-separated values (SPEED:45,DISTANCE:30,CONFIDENCE:0.95)
            elif ',' in data_string and ':' in data_string:
                parsed = {}
                parts = data_string.split(',')
                
                for part in parts:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        key = key.strip().lower()
                        
                        try:
                            # Try to convert to appropriate type
                            if key in ['speed', 'velocity']:
                                parsed['speed'] = float(value)
                            elif key in ['distance', 'range']:
                                parsed['distance'] = float(value)
                            elif key in ['confidence', 'certainty']:
                                parsed['confidence'] = float(value)
                            elif key in ['type', 'object_type']:
                                parsed['object_type'] = value.strip()
                        except ValueError:
                            logger.warning(f"Could not parse value for {key}: {value}")
                
                if parsed:
                    # Add timestamp and default values
                    parsed['timestamp'] = datetime.now().isoformat()
                    parsed.setdefault('object_type', 'Unknown')
                    parsed.setdefault('confidence', 0.8)
                    return parsed
            
            # Format 3: Space-separated values (45 30 0.95)
            elif len(data_string.split()) >= 2:
                values = data_string.split()
                return {
                    'speed': float(values[0]),
                    'distance': float(values[1]),
                    'confidence': float(values[2]) if len(values) > 2 else 0.8,
                    'object_type': 'Vehicle',
                    'timestamp': datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Data parsing error: {e}")
        
        return None
    
    def read_data_loop(self):
        """Continuous data reading loop"""
        while self.is_running and self.connection and self.connection.is_open:
            try:
                if self.connection.in_waiting > 0:
                    # Read line from sensor
                    raw_data = self.connection.readline().decode('utf-8', errors='ignore')
                    
                    if raw_data:
                        # Parse the data
                        parsed_data = self.parse_data(raw_data)
                        
                        if parsed_data and self.data_callback:
                            self.data_callback(parsed_data)
                
                time.sleep(0.1)  # Small delay
                
            except Exception as e:
                logger.error(f"Data reading error: {e}")
                time.sleep(1)
    
    def start_reading(self):
        """Start reading data in a separate thread"""
        if not self.connection or not self.connection.is_open:
            logger.error("Sensor not connected")
            return False
        
        self.is_running = True
        read_thread = threading.Thread(target=self.read_data_loop)
        read_thread.daemon = True
        read_thread.start()
        
        logger.info("Started radar sensor data reading")
        return True
    
    def stop_reading(self):
        """Stop reading data"""
        self.is_running = False
        logger.info("Stopped radar sensor data reading")
    
    def send_command(self, command):
        """Send command to the sensor"""
        if not self.connection or not self.connection.is_open:
            return False
        
        try:
            self.connection.write(f"{command}\n".encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Command send error: {e}")
            return False
    
    def get_status(self):
        """Get sensor status"""
        return {
            'connected': self.connection is not None and self.connection.is_open,
            'port': self.port,
            'baud_rate': self.baud_rate,
            'is_reading': self.is_running
        }