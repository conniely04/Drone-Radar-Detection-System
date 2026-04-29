"""
detector.py

Overall Goal:
Run the trained YOLO drone detector on each frame and return
bounding boxes in the same format as before: (x, y, w, h)

This lets the rest of the system (tracker + alert) stay the same.
"""

import logging
import os
from pathlib import Path

import cv2

logger = logging.getLogger(__name__)

_model = None
_model_error = None
_last_raw_count = 0
_last_kept_count = 0
_last_rejections = []


def _default_model_path():
    return Path(__file__).resolve().with_name("drone_best.pt")


def _get_model():
    """Load the YOLO model lazily so the Flask app can start even if vision deps are missing."""
    global _model, _model_error

    if _model is not None:
        return _model
    if _model_error is not None:
        return None

    model_path = Path(os.environ.get("DRONE_MODEL_PATH", _default_model_path()))

    try:
        from ultralytics import YOLO

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        _model = YOLO(str(model_path))
        logger.info("Loaded drone detector model from %s", model_path)
        return _model
    except Exception as exc:
        _model_error = exc
        logger.error("Drone detector unavailable: %s", exc)
        return None

def get_detector_status():
    """Expose model status for backend diagnostics."""
    return {
        "model_loaded": _model is not None,
        "model_error": str(_model_error) if _model_error else None,
        "model_path": str(Path(os.environ.get("DRONE_MODEL_PATH", _default_model_path()))),
        "last_raw_count": _last_raw_count,
        "last_kept_count": _last_kept_count,
        "last_rejections": _last_rejections,
    }


def detect(frame, conf_threshold=0.30, min_size=8, max_size_ratio=1.0):
    """
    Input:
        frame = one image from the video stream (OpenCV BGR image)

    Output:
        boxes = list of bounding boxes (x, y, w, h)
    """
    global _last_raw_count, _last_kept_count, _last_rejections

    boxes = []
    _last_rejections = []
    model = _get_model()
    if model is None:
        _last_raw_count = 0
        _last_kept_count = 0
        _last_rejections = ["model unavailable"]
        return boxes

    frame_h, frame_w = frame.shape[:2]

    # Convert BGR -> RGB because YOLO expects RGB-style input
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Run inference
    results = model(frame_rgb, verbose=False)

    for result in results:
        _last_raw_count = len(result.boxes)
        for box in result.boxes:
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])

            # Keep only class 0 (drone) and only confident detections
            if class_id != 0:
                _last_rejections.append(f"class {class_id} is not drone")
                continue
            if confidence < conf_threshold:
                _last_rejections.append(f"confidence {confidence:.2f} below {conf_threshold:.2f}")
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            x = int(x1)
            y = int(y1)
            w = int(x2 - x1)
            h = int(y2 - y1)

            # Ignore absurdly tiny boxes
            if w < min_size or h < min_size:
                _last_rejections.append(f"box {w}x{h} below min size {min_size}")
                continue

            # Ignore absurdly huge boxes
            if w > frame_w * max_size_ratio or h > frame_h * max_size_ratio:
                _last_rejections.append(f"box {w}x{h} above max ratio {max_size_ratio}")
                continue

            boxes.append((x, y, w, h))

    _last_kept_count = len(boxes)
    return boxes
