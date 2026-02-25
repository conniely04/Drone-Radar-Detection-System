import os

class Config:
    # Flask settings
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Camera settings
    CAMERA_WIDTH = int(os.environ.get('CAMERA_WIDTH', 640))
    CAMERA_HEIGHT = int(os.environ.get('CAMERA_HEIGHT', 480))
    CAMERA_FPS = int(os.environ.get('CAMERA_FPS', 30))
    CAMERA_DEVICE = int(os.environ.get('CAMERA_DEVICE', 0))
    
    # Serial/UART settings
    SERIAL_PORT = os.environ.get('SERIAL_PORT', None)  # Auto-detect if None
    BAUD_RATE = int(os.environ.get('BAUD_RATE', 9600))
    SERIAL_TIMEOUT = float(os.environ.get('SERIAL_TIMEOUT', 1.0))
    
    # Data storage settings
    MAX_DETECTIONS = int(os.environ.get('MAX_DETECTIONS', 100))
    
    # Raspberry Pi specific settings
    ENABLE_PI_CAMERA = os.environ.get('ENABLE_PI_CAMERA', 'True').lower() == 'true'
    PI_CAMERA_RESOLUTION = (CAMERA_WIDTH, CAMERA_HEIGHT)
    PI_CAMERA_FRAMERATE = CAMERA_FPS