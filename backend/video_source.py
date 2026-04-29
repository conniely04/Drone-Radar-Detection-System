"""
video_source.py
Handles video input for both:
- Mac (OpenCV webcam)
- Raspberry Pi (Picamera2)
"""

import logging
import time

import cv2

logger = logging.getLogger(__name__)

def start_video(source=0, width=640, height=480, fps=30):
    """
    Automatically chooses:
    - Picamera2 if available (Raspberry Pi)
    - OpenCV webcam otherwise (Mac)
    """

    # Try Raspberry Pi camera first
    try:
        from picamera2 import Picamera2
        logger.info("Using Raspberry Pi Camera (Picamera2)")

        picam2 = Picamera2()
        config = picam2.create_video_configuration(
            main={"format": "RGB888", "size": (width, height)}
        )
        picam2.configure(config)
        picam2.start()
        time.sleep(1)

        return picam2

    except Exception as exc:
        logger.info("Picamera2 unavailable, using OpenCV camera: %s", exc)

        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            logger.error("Could not open video source %s", source)
            return None

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        return cap


def read_frame(source):
    """Read one frame from either Picamera2 or an OpenCV VideoCapture."""
    if source is None:
        return False, None

    if hasattr(source, "capture_array"):
        frame = source.capture_array()
        # Picamera2 RGB888 frames need conversion before OpenCV drawing/JPEG encoding.
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return True, frame

    return source.read()


def stop_video(source):
    """Release either Picamera2 or OpenCV camera resources."""
    if source is None:
        return

    if hasattr(source, "stop"):
        try:
            source.stop()
        except Exception as exc:
            logger.warning("Error stopping camera source: %s", exc)

        if hasattr(source, "close"):
            try:
                source.close()
            except Exception as exc:
                logger.warning("Error closing camera source: %s", exc)
    elif hasattr(source, "release"):
        source.release()
