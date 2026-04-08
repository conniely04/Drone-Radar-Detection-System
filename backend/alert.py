"""
alert.py

Overall Goal:
This module decides when to trigger an "alert event".

It uses tracked object data (ID, how long it's been seen, speed)
to avoid false positives and avoid saving too many images.

When an object meets the rules:
- Save a screenshot to the runs/ folder
- Print an alert message to the terminal

This turns the vision pipeline into an event-driven system.
"""

import os    # used to create folders / manage file paths
import time  # used for timestamps + cooldown timing
import cv2   # used to save images (cv2.imwrite)

# -------------------------
# GLOBAL STATE (memory)
# -------------------------

# Stores when the LAST alert happened (used for cooldown)
last_alert_time = 0.0

# For each object ID, store how many frames in a row the speed has been "good"
# Example: speed_ok_streak[3] = 5 means object ID 3 had valid speed for 5 frames straight
speed_ok_streak = {}

# Stores IDs that have already triggered an alert, so we don't alert repeatedly for same object
alerted_ids = set()


def check_and_alert(
    tracked_objects,       # list of tracked objects from tracker.py
    frame,                 # current video frame (image) we might save
    confirm_frames=8,      # must exist this many frames to be "real"
    min_speed=2,           # too slow = probably noise or not drone-like
    max_speed=60,          # too fast = probably tracker glitch / teleport
    streak_needed=3,       # speed must be in-range for this many frames in a row
    cooldown_seconds=2.0,  # minimum time between saved alerts (prevents spam)
    out_dir="runs"         # folder where saved images go
):
    """
    Input:
      tracked_objects = [(obj_id, x, y, w, h, count, speed), ...]
      frame = current image from camera

    Behavior:
      If an object is stable enough, save evidence screenshot + print alert.
    """
    global last_alert_time, speed_ok_streak, alerted_ids

    # Make sure output folder exists (if it doesn't, create it)
    os.makedirs(out_dir, exist_ok=True)

    # Current time (seconds since epoch), used for cooldown
    now = time.time()

    # Go through each tracked object
    for (obj_id, x, y, w, h, count, speed) in tracked_objects:

        # -------------------------
        # 1) Update speed streak
        # -------------------------

        # If speed is in the desired range, increment streak counter for this ID
        if min_speed < speed < max_speed:
            speed_ok_streak[obj_id] = speed_ok_streak.get(obj_id, 0) + 1
        else:
            # If speed is out of range, reset the streak to 0
            speed_ok_streak[obj_id] = 0

        # -------------------------
        # 2) Alert decision rules
        # -------------------------

        # Only alert when ALL conditions are true:
        # - object persisted long enough (count >= confirm_frames)
        # - speed has been stable in range for streak_needed frames
        # - enough time passed since last alert (cooldown)
        # - this ID hasn't already triggered an alert
        if (
            count >= confirm_frames
            and speed_ok_streak.get(obj_id, 0) >= streak_needed
            and (now - last_alert_time) >= cooldown_seconds
            and obj_id not in alerted_ids
        ):
            # Mark this object ID as alerted so it won't alert again
            alerted_ids.add(obj_id)

            # Update global cooldown timer
            last_alert_time = now

            # Create a timestamp string for filenames (YYYYMMDD_HHMMSS)
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            # Build the output filename that includes the object ID
            filename = f"{out_dir}/alert_id{obj_id}_{timestamp}.jpg"

            # Save the current frame as evidence image
            cv2.imwrite(filename, frame)

            # Print an alert message for debugging / logging
            print(
                f"🚨 ALERT (cooldown ok) | ID {obj_id} | speed={int(speed)} "
                f"| streak={speed_ok_streak[obj_id]} | saved: {filename}"
            )


            