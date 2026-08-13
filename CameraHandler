import cv2
import face_recognition
import pickle
import os

ENCODINGS_FILE = "known_faces.pkl"

# 1. Load your saved face dataset
if not os.path.exists(ENCODINGS_FILE):
    print(f"❌ Error: Could not find '{ENCODINGS_FILE}'. Please run your registration script first!")
    exit()

print("Loading saved patient encodings...")
with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.load(f)

known_encodings = data["encodings"]
known_names = data["names"]

# 2. Open the Raspberry Pi Camera
cap = cv2.VideoCapture(0)

# Optional Pi Camera tweak: set lower resolution for speed
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("📷 Camera active! Looking for faces... (Press Ctrl + C in terminal to stop)\n")

last_printed_name = None  # Prevents spamming the terminal repeatedly for the same face

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Resize frame to 1/4 size to speed up Raspberry Pi processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detect face locations and generate live encodings
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        # If no faces are in front of the camera, reset tracker
        if not face_encodings:
            last_printed_name = None
            continue

        for face_encoding in face_encodings:
            # Compare the live face against saved encodings
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
            name = "Unknown Face"

            if True in matches:
                matched_index = matches.index(True)
                name = known_names[matched_index]

            # Print to terminal only when a new face appears or status changes
            if name != last_printed_name:
                if name != "Unknown Face":
                    print(f"🟢 RECOGNIZED PATIENT: {name}")
                else:
                    print("🔴 WARNING: Unknown Face Detected")
                
                last_printed_name = name

except KeyboardInterrupt:
    print("\nShutting down camera feed...")

finally:
    cap.release()
    cv2.destroyAllWindows()
