"""
main.py (Overall)

This file runs the entire real-time vision system loop.

It connects these parts together:
1) Video source (camera) -> gives frames
2) Detector -> finds moving objects (returns bounding boxes)
3) Tracker -> gives each object an ID, counts how long it persists, estimates speed
4) Alert -> saves evidence when an object looks "confirmed"
5) Display -> draws boxes/labels so you can see what’s happening live

Think of main.py as the "manager" that tells all other modules what to do each frame.
"""

import cv2
from video_source import start_video
from detector import detect
from tracker import update
from alert import check_and_alert

def main():
    # Start the camera/video stream
    cap = start_video(0)

    # Infinite loop: each iteration processes one video frame
    while True:
        # If using Raspberry Pi camera, use capture_array()
        if hasattr(cap, "capture_array"):
            frame = cap.capture_array()
            ret = True
        else:
            # Otherwise use standard OpenCV webcam
            ret, frame = cap.read()

        # If frame grab failed, stop
        if not ret:
            break

        # Run detection
        boxes = detect(frame)

        # Run tracking
        tracked = update(boxes)

        # Draw tracking results
        for (obj_id, x, y, w, h, count, speed) in tracked:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            label = f"ID {obj_id} seen {count} speed {int(speed)}"
            cv2.putText(
                frame, label, (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
            )

            if count >= 8:
                cv2.putText(
                    frame, "CONFIRMED", (x, y + h + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                )

        # Alert logic
        check_and_alert(tracked, frame)

        # Show result
        cv2.imshow("Drone Detection - Filtering + Tracking", frame)

        # Quit if q is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Clean up camera resource
    if hasattr(cap, "stop"):
        cap.stop()
    else:
        cap.release()

    # Close windows
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()