"""
video_source.py
Handles video input for both:
- Mac (OpenCV webcam)
- Raspberry Pi (Picamera2)
"""

import cv2

def start_video(source=0):
    """
    Automatically chooses:
    - Picamera2 if available (Raspberry Pi)
    - OpenCV webcam otherwise (Mac)
    """

    # Try Raspberry Pi camera first
    try:
        from picamera2 import Picamera2
        import time

        print("Using Raspberry Pi Camera (Picamera2)")

        picam2 = Picamera2()
        config = picam2.create_preview_configuration(
            main={"format": "RGB888"}
        )
        picam2.configure(config)
        picam2.start()
        time.sleep(1)

        return picam2

    except Exception:
        print("Picamera2 not found, using OpenCV webcam")

        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            print("Error: Could not open video source.")
            exit()

        return cap