import cv2
import face_recognition
import pickle
import os
import time
from picamera2 import Picamera2


# ============================================================
# SETTINGS
# ============================================================

ENCODINGS_FILE = "known_face.pkl"


# ============================================================
# 1. LOAD SAVED FACE DATASET
# ============================================================

if not os.path.exists(ENCODINGS_FILE):
    print(f"❌ ERROR: Could not find '{ENCODINGS_FILE}'.")
    print("Make sure known_face.pkl is in the same folder.")
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
# 2. START RASPBERRY PI CAMERA
# ============================================================

print("\n📷 Starting Raspberry Pi Camera...")

try:

    picam2 = Picamera2()

    camera_config = picam2.create_preview_configuration(
        main={
            "size": (640, 480),
            "format": "RGB888"
        }
    )

    picam2.configure(camera_config)

    picam2.start()

    # Give the camera time to start
    time.sleep(2)

    print("✅ CAMERA CONNECTED!")
    print("🟢 CAMERA IS NOW ACTIVE")
    print("🔴 Press Q to stop.")
    print("==============================================\n")

except Exception as e:

    print("❌ ERROR: Could not start Raspberry Pi Camera!")
    print()
    print("Camera error:")
    print(e)
    print()
    print("Make sure your ribbon camera is connected.")
    exit()


# ============================================================
# 3. VARIABLES
# ============================================================

last_printed_name = None

frame_count = 0
start_time = time.time()


# ============================================================
# 4. MAIN LOOP
# ============================================================

try:

    while True:

        # ----------------------------------------------------
        # Capture image from Raspberry Pi Camera
        # ----------------------------------------------------

        frame = picam2.capture_array()

        if frame is None:
            print("⚠️ Failed to capture frame.")
            continue

        frame_count += 1


        # ----------------------------------------------------
        # Resize for faster face recognition
        # ----------------------------------------------------

        small_frame = cv2.resize(
            frame,
            (0, 0),
            fx=0.25,
            fy=0.25
        )


        # Picamera2 RGB888 already gives RGB
        rgb_small_frame = small_frame


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


        # ====================================================
        # CAMERA STATUS
        # ====================================================

        cv2.putText(
            frame,
            "CAMERA ACTIVE",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )


        # ====================================================
        # FPS
        # ====================================================

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


        # ====================================================
        # NO FACE
        # ====================================================

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

            last_printed_name = None


        # ====================================================
        # FACE DETECTED
        # ====================================================

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


            # ------------------------------------------------
            # Process each detected face
            # ------------------------------------------------

            for face_encoding, face_location in zip(
                face_encodings,
                face_locations
            ):


                # ============================================
                # COMPARE FACE
                # ============================================

                matches = face_recognition.compare_faces(
                    known_encodings,
                    face_encoding,
                    tolerance=0.5
                )


                name = "Unknown Face"


                # ============================================
                # FIND MATCH
                # ============================================

                if True in matches:

                    matched_index = matches.index(True)

                    name = known_names[matched_index]


                # ============================================
                # PRINT RECOGNITION RESULT
                # ============================================

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


                # ============================================
                # FACE COORDINATES
                # ============================================

                top, right, bottom, left = face_location


                # Because the image was resized to 1/4
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4


                # ============================================
                # BOX COLOR
                # ============================================

                if name == "Unknown Face":

                    color = (0, 0, 255)

                else:

                    color = (0, 255, 0)


                # ============================================
                # FACE BOX
                # ============================================

                cv2.rectangle(
                    frame,
                    (left, top),
                    (right, bottom),
                    color,
                    2
                )


                # ============================================
                # NAME BACKGROUND
                # ============================================

                cv2.rectangle(
                    frame,
                    (left, bottom - 35),
                    (right, bottom),
                    color,
                    cv2.FILLED
                )


                # ============================================
                # NAME
                # ============================================

                cv2.putText(
                    frame,
                    name,
                    (left + 6, bottom - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1
                )


        # ====================================================
        # SHOW CAMERA
        # ====================================================

        cv2.imshow(
            "Patient Face Recognition",
            frame
        )


        # ====================================================
        # KEYBOARD INPUT
        # ====================================================

        key = cv2.waitKey(1) & 0xFF


        if key == ord("q"):

            print("\n🛑 Stop command received.")

            break


# ============================================================
# 5. CTRL+C
# ============================================================

except KeyboardInterrupt:

    print("\n🛑 Keyboard interrupt received.")


# ============================================================
# 6. CLEANUP
# ============================================================

finally:

    print("📷 Stopping Raspberry Pi Camera...")

    try:

        picam2.stop()

    except:

        pass


    cv2.destroyAllWindows()

    print("✅ Camera stopped.")
    print("👋 Face recognition system shut down.")
