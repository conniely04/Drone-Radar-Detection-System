import base64
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

from detector import detect
from tracker import update

logger = logging.getLogger(__name__)
SNAPSHOT_DIR = Path(__file__).resolve().with_name("runs")
SNAPSHOT_DIR.mkdir(exist_ok=True)


def _decode_base64_image(image_base64: str):
    """Decode a base64 image string into an OpenCV BGR frame."""
    if not image_base64:
        return None

    # Accept both raw base64 and data URL formats.
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception:
        return None

    np_arr = np.frombuffer(image_bytes, dtype=np.uint8)
    if np_arr.size == 0:
        return None

    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)


class VisionProcessor:
    """Run drone detection/tracking on camera frames and draw stream overlays."""

    def __init__(self, confirm_frames: int = 3, report_cooldown_seconds: float = 2.0):
        self.confirm_frames = confirm_frames
        self.report_cooldown_seconds = report_cooldown_seconds
        self.last_report_by_id: Dict[int, float] = {}
        self.saved_snapshot_ids = set()
        self.latest: Dict[str, Any] = {
            "detections": [],
            "drone_detected": False,
            "count": 0,
            "timestamp": None,
        }

    def process_frame(self, frame) -> Tuple[Any, List[Dict[str, Any]]]:
        """Process one OpenCV BGR frame and return the annotated frame plus new events."""
        if frame is None:
            return frame, []

        try:
            boxes = detect(frame)
            tracked = update(boxes)
            new_events = self._tracked_to_events(tracked)
            self._draw_overlay(frame, tracked)
            self._save_confirmed_snapshots(tracked, frame)
            confirmed = [
                item for item in tracked
                if item[5] >= self.confirm_frames
            ]

            self.latest = {
                "detections": [self._tracked_to_detection(item) for item in tracked],
                "drone_detected": bool(confirmed),
                "count": len(tracked),
                "confirmed_count": len(confirmed),
                "timestamp": datetime.now().isoformat(),
            }
            return frame, new_events
        except Exception as exc:
            logger.error("Vision processing error: %s", exc, exc_info=True)
            self.latest = {
                "detections": [],
                "drone_detected": False,
                "count": 0,
                "timestamp": datetime.now().isoformat(),
                "error": str(exc),
            }
            return frame, []

    def _tracked_to_detection(self, tracked_item) -> Dict[str, Any]:
        obj_id, x, y, w, h, count, speed = tracked_item
        return {
            "track_id": obj_id,
            "bbox": {"x": x, "y": y, "width": w, "height": h},
            "track_count": count,
            "speed": float(speed),
            "unit": "px/frame",
            "object_type": "Drone",
        }

    def _tracked_to_events(self, tracked) -> List[Dict[str, Any]]:
        now = time.time()
        events = []

        for item in tracked:
            obj_id, x, y, w, h, count, speed = item
            last_report = self.last_report_by_id.get(obj_id, 0)
            if count < self.confirm_frames or (now - last_report) < self.report_cooldown_seconds:
                continue

            self.last_report_by_id[obj_id] = now
            events.append(
                {
                    "source": "vision",
                    "object_type": "Drone",
                    "track_id": obj_id,
                    "speed": float(speed),
                    "unit": "px/frame",
                    "confidence": None,
                    "distance": None,
                    "computed_distance": None,
                    "computed_distance_unit": None,
                    "bbox": {"x": x, "y": y, "width": w, "height": h},
                    "track_count": count,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return events

    def _save_confirmed_snapshots(self, tracked, frame) -> None:
        """Save one snapshot per track as soon as it reaches the confirmation count."""
        for obj_id, _x, _y, _w, _h, count, _speed in tracked:
            if count < self.confirm_frames or obj_id in self.saved_snapshot_ids:
                continue

            self.saved_snapshot_ids.add(obj_id)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = SNAPSHOT_DIR / f"alert_id{obj_id}_{timestamp}.jpg"

            if cv2.imwrite(str(filename), frame):
                logger.info("Saved drone snapshot: %s", filename)
            else:
                logger.error("Failed to save drone snapshot: %s", filename)

    def _draw_overlay(self, frame, tracked) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            frame,
            timestamp,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        if not tracked:
            cv2.putText(
                frame,
                "Scanning for drones",
                (10, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )
            return

        for obj_id, x, y, w, h, count, speed in tracked:
            confirmed = count >= self.confirm_frames
            color = (0, 0, 255) if confirmed else (0, 255, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            label = f"{'Drone' if confirmed else 'Candidate'} ID {obj_id} seen {count}"
            cv2.putText(
                frame,
                label,
                (x, max(20, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

            if confirmed:
                cv2.putText(
                    frame,
                    "CONFIRMED",
                    (x, min(frame.shape[0] - 10, y + h + 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2,
                )


def detect_drone_in_frame(image_base64: str) -> Dict[str, Any]:
    """Detect drones in a base64 image using the same backend vision pipeline."""
    frame = _decode_base64_image(image_base64)

    if frame is None:
        return {
            "detections": [],
            "drone_detected": False,
            "count": 0,
            "error": "Invalid or unsupported image data",
        }

    boxes = detect(frame)
    detections: List[Dict[str, Any]] = [
        {
            "bbox": {"x": x, "y": y, "width": w, "height": h},
            "object_type": "Drone",
            "confidence": None,
        }
        for x, y, w, h in boxes
    ]

    return {
        "detections": detections,
        "drone_detected": len(detections) > 0,
        "count": len(detections),
    }
