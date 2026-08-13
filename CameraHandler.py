import cv2
import face_recognition
import pickle
import os
from picamera2 import Picamera2

# ============================================================
# SETTINGS
# ============================================================

ENCODINGS_FILE = "known_face.pkl"

# ============================================================
# 1. LOAD SAVED FACE DATA
# ============================================================

if not os.path.exists(ENCODINGS_FILE):
    print(f"❌ Error: Could not find '{ENCODINGS_FILE}'.")
    print("Make sure known_face.pkl is in the same folder as this program.")
    exit()

print("Loading saved patient encodings...")

with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.load(f)

known_encodings = data["encodings"]
known_names = data["names"]

print(f"✅ Loaded {len(known_names)} known face(s).")

# ============================================================
# 2. START RASPBERRY PI CAMERA
# ============================================================

print("Starting Raspberry Pi Camera...")

picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={
        "size": (640, 480),
        "format": "RGB888"
    }
)

picam2.configure(config)
picam2.start()

print("📷 Camera active! Looking for faces...")
print("Press Ctrl + C to stop.\n")

# ============================================================
# 3. FACE RECOGNITION LOOP
# ============================================================

last_printed_name = None

try:

    while True:

        # Capture frame from Raspberry Pi Camera
        frame = picam2.capture_array()

        # Resize to 1/4 for faster face recognition
        small_frame = cv2.resize(
            frame,
            (0, 0),
            fx=0.25,
            fy=0.25
        )

        # Picamera2 gives RGB already
        rgb_small_frame = small_frame

        # Find faces
        face_locations = face_recognition.face_locations(
            rgb_small_frame
        )

        # Generate face encodings
        face_encodings = face_recognition.face_encodings(
            rgb_small_frame,
            face_locations
        )

        # No faces detected
        if not face_encodings:
            last_printed_name = None
            continue

        # Check every detected face
        for face_encoding in face_encodings:

            matches = face_recognition.compare_faces(
                known_encodings,
                face_encoding,
                tolerance=0.5
            )

            name = "Unknown Face"

            # If a match exists
            if True in matches:

                matched_index = matches.index(True)

                name = known_names[matched_index]

            # Only print when status changes
            if name != last_printed_name:

                if name != "Unknown Face":

                    print(
                        f"🟢 RECOGNIZED PATIENT: {name}"
                    )

                else:

                    print(
                        "🔴 WARNING: Unknown Face Detected"
                    )

                last_printed_name = name

except KeyboardInterrupt:

    print("\nStopping camera...")

finally:

    picam2.stop()

    cv2.destroyAllWindows()

    print("Camera stopped.")
