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

logger = logging.getLogger(__name__)

_model = None
_model_error = None
_fallback_model = None
_fallback_model_error = None
_last_raw_count = 0
_last_kept_count = 0
_last_rejections = []
_last_predictions = []
_last_detector_source = None

FALLBACK_AERIAL_CLASSES = {"airplane", "bird", "kite"}


def _default_model_path():
    return Path(__file__).resolve().with_name("drone_best.pt")


def _default_fallback_model_path():
    return Path(__file__).resolve().parent.parent / "yolov8n.pt"


def _get_model(model_kind="primary"):
    """Load the YOLO model lazily so the Flask app can start even if vision deps are missing."""
    global _model, _model_error, _fallback_model, _fallback_model_error

    is_fallback = model_kind == "fallback"
    cached_model = _fallback_model if is_fallback else _model
    cached_error = _fallback_model_error if is_fallback else _model_error
    if cached_model is not None:
        return cached_model
    if cached_error is not None:
        return None

    env_key = "DRONE_FALLBACK_MODEL_PATH" if is_fallback else "DRONE_MODEL_PATH"
    default_path = _default_fallback_model_path() if is_fallback else _default_model_path()
    model_path = Path(os.environ.get(env_key, default_path))

    try:
        from ultralytics import YOLO

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        loaded_model = YOLO(str(model_path))
        if is_fallback:
            _fallback_model = loaded_model
        else:
            _model = loaded_model
        logger.info("Loaded %s detector model from %s", model_kind, model_path)
        return loaded_model
    except Exception as exc:
        if is_fallback:
            _fallback_model_error = exc
        else:
            _model_error = exc
        logger.error("%s detector unavailable: %s", model_kind.title(), exc)
        return None

def get_detector_status():
    """Expose model status for backend diagnostics."""
    return {
        "model_loaded": _model is not None,
        "model_error": str(_model_error) if _model_error else None,
        "model_path": str(Path(os.environ.get("DRONE_MODEL_PATH", _default_model_path()))),
        "model_names": getattr(_model, "names", None) if _model is not None else None,
        "fallback_enabled": os.environ.get("DRONE_USE_FALLBACK", "true").lower() != "false",
        "fallback_model_loaded": _fallback_model is not None,
        "fallback_model_error": str(_fallback_model_error) if _fallback_model_error else None,
        "fallback_model_path": str(Path(os.environ.get("DRONE_FALLBACK_MODEL_PATH", _default_fallback_model_path()))),
        "fallback_model_names": getattr(_fallback_model, "names", None) if _fallback_model is not None else None,
        "last_raw_count": _last_raw_count,
        "last_kept_count": _last_kept_count,
        "last_rejections": _last_rejections,
        "last_predictions": _last_predictions,
        "last_detector_source": _last_detector_source,
    }


def _drone_class_ids(model):
    """Return class IDs that look like drone classes, or None for one-class models."""
    names = getattr(model, "names", None)
    if not names:
        return None

    if isinstance(names, dict):
        items = names.items()
    else:
        items = enumerate(names)

    matching_ids = {
        int(class_id)
        for class_id, name in items
        if "drone" in str(name).lower() or "uav" in str(name).lower()
    }
    return matching_ids or None


def _fallback_class_ids(model):
    names = getattr(model, "names", None)
    if not names:
        return None

    if isinstance(names, dict):
        items = names.items()
    else:
        items = enumerate(names)

    return {
        int(class_id)
        for class_id, name in items
        if str(name).lower() in FALLBACK_AERIAL_CLASSES
    }


def _class_name(model, class_id):
    names = getattr(model, "names", {})
    if isinstance(names, dict):
        return names.get(class_id, str(class_id))
    if isinstance(names, (list, tuple)) and 0 <= class_id < len(names):
        return names[class_id]
    return str(class_id)


def _run_model(frame, model, allowed_class_ids, conf_threshold, min_size, max_size_ratio, source):
    global _last_raw_count, _last_rejections, _last_predictions

    boxes = []
    frame_h, frame_w = frame.shape[:2]
    results = model(frame, conf=0.01, verbose=False)

    for result in results:
        _last_raw_count += len(result.boxes)
        for box in result.boxes:
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = _class_name(model, class_id)
            _last_predictions.append(
                {
                    "source": source,
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": round(confidence, 4),
                }
            )

            if allowed_class_ids is not None and class_id not in allowed_class_ids:
                _last_rejections.append(f"{source}: class {class_id} ({class_name}) is not drone-like")
                continue
            if confidence < conf_threshold:
                _last_rejections.append(f"{source}: confidence {confidence:.2f} below {conf_threshold:.2f}")
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            x = int(x1)
            y = int(y1)
            w = int(x2 - x1)
            h = int(y2 - y1)

            if w < min_size or h < min_size:
                _last_rejections.append(f"{source}: box {w}x{h} below min size {min_size}")
                continue

            if w > frame_w * max_size_ratio or h > frame_h * max_size_ratio:
                _last_rejections.append(f"{source}: box {w}x{h} above max ratio {max_size_ratio}")
                continue

            boxes.append((x, y, w, h))

    return boxes


def detect(frame, conf_threshold=None, min_size=8, max_size_ratio=1.0):
    """
    Input:
        frame = one image from the video stream (OpenCV BGR image)

    Output:
        boxes = list of bounding boxes (x, y, w, h)
    """
    global _last_raw_count, _last_kept_count, _last_rejections, _last_predictions, _last_detector_source

    boxes = []
    _last_raw_count = 0
    _last_kept_count = 0
    _last_rejections = []
    _last_predictions = []
    _last_detector_source = None
    model = _get_model()
    if model is None:
        _last_rejections = ["model unavailable"]
        return boxes

    if conf_threshold is None:
        conf_threshold = float(os.environ.get("DRONE_CONF_THRESHOLD", "0.15"))

    allowed_class_ids = _drone_class_ids(model)
    boxes = _run_model(
        frame,
        model,
        allowed_class_ids,
        conf_threshold,
        min_size,
        max_size_ratio,
        "primary",
    )

    if not boxes and os.environ.get("DRONE_USE_FALLBACK", "true").lower() != "false":
        fallback_model = _get_model("fallback")
        if fallback_model is not None:
            fallback_threshold = float(os.environ.get("DRONE_FALLBACK_CONF_THRESHOLD", "0.20"))
            fallback_boxes = _run_model(
                frame,
                fallback_model,
                _fallback_class_ids(fallback_model),
                fallback_threshold,
                min_size,
                max_size_ratio,
                "fallback",
            )
            if fallback_boxes:
                boxes = fallback_boxes
                _last_detector_source = "fallback"

    if boxes and _last_detector_source is None:
        _last_detector_source = "primary"

    _last_kept_count = len(boxes)
    return boxes
