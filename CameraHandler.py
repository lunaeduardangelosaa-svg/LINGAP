import cv2
import face_recognition
import pickle
import os
import time

ENCODINGS_FILE = "known_face.pkl"

# ============================================================
# 1. LOAD SAVED FACE DATASET
# ============================================================

if not os.path.exists(ENCODINGS_FILE):
    print(f"❌ ERROR: Could not find '{ENCODINGS_FILE}'.")
    print("Please run your registration script first!")
    exit()

print("==============================================")
print("     PATIENT FACE RECOGNITION SYSTEM")
print("==============================================")
print("📂 Loading saved patient encodings...")

with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.load(f)

known_encodings = data["encodings"]
known_names = data["names"]

print(f"✅ Loaded {len(known_names)} registered face(s).")

# ============================================================
# 2. OPEN CAMERA
# ============================================================

print("\n📷 Starting camera...")

cap = cv2.VideoCapture(0)

# Camera resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Check if camera actually opened
if not cap.isOpened():
    print("❌ ERROR: Could not open camera!")
    print("Check that your Raspberry Pi camera/USB camera is connected.")
    exit()

print("✅ CAMERA CONNECTED!")
print("🟢 CAMERA IS NOW ACTIVE")
print("🔴 Press 'q' in the camera window to stop.")
print("==============================================\n")

# ============================================================
# 3. VARIABLES
# ============================================================

last_printed_name = None
frame_count = 0
start_time = time.time()

# ============================================================
# 4. MAIN CAMERA LOOP
# ============================================================

try:

    while True:

        # Read frame from camera
        ret, frame = cap.read()

        # Check if camera is still working
        if not ret:
            print("⚠️ WARNING: Failed to read camera frame!")
            continue

        frame_count += 1

        # ----------------------------------------------------
        # Resize frame for faster face recognition
        # ----------------------------------------------------

        small_frame = cv2.resize(
            frame,
            (0, 0),
            fx=0.25,
            fy=0.25
        )

        # Convert BGR -> RGB
        rgb_small_frame = cv2.cvtColor(
            small_frame,
            cv2.COLOR_BGR2RGB
        )

        # ----------------------------------------------------
        # Detect faces
        # ----------------------------------------------------

        face_locations = face_recognition.face_locations(
            rgb_small_frame
        )

        face_encodings = face_recognition.face_encodings(
            rgb_small_frame,
            face_locations
        )

        # ----------------------------------------------------
        # Camera status
        # ----------------------------------------------------

        cv2.putText(
            frame,
            "CAMERA ACTIVE",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        # ----------------------------------------------------
        # Calculate FPS
        # ----------------------------------------------------

        elapsed_time = time.time() - start_time

        if elapsed_time > 0:
            fps = frame_count / elapsed_time
        else:
            fps = 0

        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (20, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        # ----------------------------------------------------
        # If NO face detected
        # ----------------------------------------------------

        if not face_encodings:

            cv2.putText(
                frame,
                "NO FACE DETECTED",
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

            # Reset previous person
            last_printed_name = None

        # ----------------------------------------------------
        # If face(s) detected
        # ----------------------------------------------------

        else:

            cv2.putText(
                frame,
                f"FACE(S) DETECTED: {len(face_encodings)}",
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

            # Process every detected face
            for face_encoding, face_location in zip(
                face_encodings,
                face_locations
            ):

                # ------------------------------------------------
                # Compare face with registered patients
                # ------------------------------------------------

                matches = face_recognition.compare_faces(
                    known_encodings,
                    face_encoding,
                    tolerance=0.5
                )

                name = "Unknown Face"

                # Find matching patient
                if True in matches:

                    matched_index = matches.index(True)

                    name = known_names[matched_index]

                # ------------------------------------------------
                # Print result only when status changes
                # ------------------------------------------------

                if name != last_printed_name:

                    if name != "Unknown Face":

                        print(
                            f"🟢 RECOGNIZED PATIENT: {name}"
                        )

                    else:

                        print(
                            "🔴 WARNING: UNKNOWN FACE DETECTED"
                        )

                    last_printed_name = name

                # ------------------------------------------------
                # Convert face coordinates back to full size
                # ------------------------------------------------

                top, right, bottom, left = face_location

                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # ------------------------------------------------
                # Choose box color
                # ------------------------------------------------

                if name == "Unknown Face":

                    color = (0, 0, 255)

                else:

                    color = (0, 255, 0)

                # ------------------------------------------------
                # Draw rectangle around face
                # ------------------------------------------------

                cv2.rectangle(
                    frame,
                    (left, top),
                    (right, bottom),
                    color,
                    2
                )

                # ------------------------------------------------
                # Draw name label
                # ------------------------------------------------

                cv2.rectangle(
                    frame,
                    (left, bottom - 35),
                    (right, bottom),
                    color,
                    cv2.FILLED
                )

                cv2.putText(
                    frame,
                    name,
                    (left + 6, bottom - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1
                )

        # ========================================================
        # SHOW CAMERA WINDOW
        # ========================================================

        cv2.imshow(
            "Patient Face Recognition - CAMERA ACTIVE",
            frame
        )

        # Press Q to stop
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):

            print("\n🛑 Stop command received.")

            break

# ============================================================
# 5. HANDLE CTRL+C
# ============================================================

except KeyboardInterrupt:

    print("\n🛑 Keyboard interrupt received.")
    print("Stopping camera...")

# ============================================================
# 6. CLEAN UP
# ============================================================

finally:

    print("📷 Releasing camera...")

    cap.release()

    cv2.destroyAllWindows()

    print("✅ Camera stopped.")
    print("👋 Face recognition system shut down.")
