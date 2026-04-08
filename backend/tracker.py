"""
tracker.py

Overall Goal:
Track detected objects across frames.

This module:
- Assigns a unique ID to each object
- Keeps track of how long the object persists (frame count)
- Estimates object speed based on center movement
- Returns enriched object data for further filtering and alerting

This converts raw motion boxes into persistent tracked objects.
"""

import math

# Global dictionary storing active tracked objects.
# Format:
# {
#   object_id: {
#       "cx": center_x,
#       "cy": center_y,
#       "count": number_of_frames_seen,
#       "speed": last_frame_movement_distance
#   }
# }
objects = {}

# Counter used to assign new unique IDs
next_id = 1


def _distance(x1, y1, x2, y2):
    """
    Compute Euclidean distance between two points.
    Used to determine how far an object moved between frames.
    """
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)


def update(boxes, max_distance=50):
    """
    Input:
        boxes = list of bounding boxes (x, y, w, h)
    
    Output:
        tracked = list of:
            (id, x, y, w, h, count, speed)

    max_distance:
        Maximum allowed movement between frames to still consider
        it the same object.
    """

    global next_id, objects

    tracked = []        # Final list of tracked objects for this frame
    used_ids = set()    # Prevent assigning same ID twice in one frame

    # Loop through each detected box
    for (x, y, w, h) in boxes:

        # Compute center of bounding box
        cx = x + w // 2
        cy = y + h // 2

        best_id = None
        best_dist = 999999

        # Compare with all previously tracked objects
        for obj_id, obj in objects.items():

            # Compute distance between current center and previous center
            dist = _distance(cx, cy, obj["cx"], obj["cy"])

            # If close enough and not already used this frame
            if dist < best_dist and dist < max_distance and obj_id not in used_ids:
                best_dist = dist
                best_id = obj_id

        if best_id is None:
            # No close object found → create new object
            obj_id = next_id
            next_id += 1

            objects[obj_id] = {
                "cx": cx,
                "cy": cy,
                "count": 1,
                "speed": 0
            }

            best_id = obj_id

        else:
            # Existing object found → update it

            prev_cx = objects[best_id]["cx"]
            prev_cy = objects[best_id]["cy"]

            # Compute speed (distance moved this frame)
            speed = _distance(cx, cy, prev_cx, prev_cy)

            # Update stored object information
            objects[best_id]["cx"] = cx
            objects[best_id]["cy"] = cy
            objects[best_id]["count"] += 1
            objects[best_id]["speed"] = speed

        # Mark this ID as used for this frame
        used_ids.add(best_id)

        # Retrieve updated values
        count = objects[best_id]["count"]
        speed = objects[best_id]["speed"]

        # Append tracking result
        tracked.append((best_id, x, y, w, h, count, speed))

    return tracked