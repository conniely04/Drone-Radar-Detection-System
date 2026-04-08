"""
detector.py

Overall Goal:
Run the trained YOLO drone detector on each frame and return
bounding boxes in the same format as before: (x, y, w, h)

This lets the rest of the system (tracker + alert) stay the same.
"""

import cv2
from ultralytics import YOLO

# Load trained model once
model = YOLO("models/drone_best.pt")

def detect(frame, conf_threshold=0.40, min_size=12, max_size_ratio=0.8):
    """
    Input:
        frame = one image from the video stream (OpenCV BGR image)

    Output:
        boxes = list of bounding boxes (x, y, w, h)
    """
    boxes = []

    frame_h, frame_w = frame.shape[:2]

    # Convert BGR -> RGB because YOLO expects RGB-style input
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Run inference
    results = model(frame_rgb, verbose=False)

    for result in results:
        for box in result.boxes:
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])

            # Keep only class 0 (drone) and only confident detections
            if class_id != 0:
                continue
            if confidence < conf_threshold:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            x = int(x1)
            y = int(y1)
            w = int(x2 - x1)
            h = int(y2 - y1)

            # Ignore absurdly tiny boxes
            if w < min_size or h < min_size:
                continue

            # Ignore absurdly huge boxes
            if w > frame_w * max_size_ratio or h > frame_h * max_size_ratio:
                continue

            boxes.append((x, y, w, h))

    return boxes