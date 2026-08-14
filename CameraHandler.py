```python
import cv2
import face_recognition
import pickle
import os
import time
import threading
from picamera2 import Picamera2


# ============================================================
# SETTINGS
# ============================================================

ENCODINGS_FILE = "known_faces.pkl"
PHOTO_FOLDER = "faces"

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

SCALE = 0.25
COUNTDOWN_SECONDS = 3

# Face recognition tolerance
# Lower = stricter
TOLERANCE = 0.5


# ============================================================
# CREATE PHOTO FOLDER
# ============================================================

if not os.path.exists(PHOTO_FOLDER):
    os.makedirs(PHOTO_FOLDER)


# ============================================================
# LOAD DATABASE
# ============================================================

if os.path.exists(ENCODINGS_FILE):

    try:

        with open(ENCODINGS_FILE, "rb") as f:
            data = pickle.load(f)

        known_encodings = data.get("encodings", [])
        known_names = data.get("names", [])

        print(
            f"✅ Loaded {len(known_names)} registered face(s)."
        )

    except Exception as e:

        print("⚠️ Database could not be loaded.")
        print(e)

        known_encodings = []
        known_names = []

else:

    print("ℹ️ No face database found.")
    print("A new database will be created.")

    known_encodings = []
    known_names = []


# ============================================================
# SAVE DATABASE
# ============================================================

def save_database():

    data = {
        "names": known_names,
        "encodings": known_encodings
    }

    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)

    print("💾 Face database saved.")


# ============================================================
# START CAMERA
# ============================================================

print()
print("==============================================")
print("   RASPBERRY PI FACE RECOGNITION SYSTEM")
print("==============================================")
print()

print("📷 Starting Raspberry Pi camera...")

try:

    picam2 = Picamera2()

    camera_config = picam2.create_preview_configuration(
        main={
            "size": (CAMERA_WIDTH, CAMERA_HEIGHT),
            "format": "RGB888"
        }
    )

    picam2.configure(camera_config)

    picam2.start()

    time.sleep(2)

    print("✅ Camera ready.")

except Exception as e:

    print("❌ Camera could not start.")
    print(e)
    exit()


# ============================================================
# CAMERA STATE
# ============================================================

mode = "idle"

running = True

countdown_active = False
countdown_start = 0

last_countdown_second = -1


# ============================================================
# PRIMARY FACE
# ============================================================

def get_primary_face(face_locations):

    if not face_locations:
        return None

    def area(location):

        top, right, bottom, left = location

        width = right - left
        height = bottom - top

        return width * height

    return max(
        face_locations,
        key=area
    )


# ============================================================
# ENROLLMENT
# ============================================================

def enroll_face(frame, face_location):

    global known_encodings
    global known_names

    print()
    print("==============================================")
    print("             FACE DETECTED")
    print("==============================================")

    # --------------------------------------------------------
    # Ask for name
    # --------------------------------------------------------

    name = input("Enter person's name: ").strip()

    if name == "":

        print("❌ Name cannot be empty.")
        return False


    # --------------------------------------------------------
    # Convert coordinates back to full resolution
    # --------------------------------------------------------

    top, right, bottom, left = face_location

    top = int(top / SCALE)
    right = int(right / SCALE)
    bottom = int(bottom / SCALE)
    left = int(left / SCALE)


    # --------------------------------------------------------
    # Add padding for saved photo
    # --------------------------------------------------------

    padding = 40

    crop_top = max(0, top - padding)
    crop_bottom = min(
        frame.shape[0],
        bottom + padding
    )

    crop_left = max(0, left - padding)
    crop_right = min(
        frame.shape[1],
        right + padding
    )


    face_photo = frame[
        crop_top:crop_bottom,
        crop_left:crop_right
    ]


    if face_photo.size == 0:

        print("❌ Could not capture face.")
        return False


    # --------------------------------------------------------
    # SAVE PHOTO
    # --------------------------------------------------------

    safe_name = "".join(
        c for c in name
        if c.isalnum() or c in (" ", "_", "-")
    ).strip()

    photo_path = os.path.join(
        PHOTO_FOLDER,
        safe_name + ".jpg"
    )

    cv2.imwrite(
        photo_path,
        face_photo
    )

    print(f"📸 Photo saved: {photo_path}")


    # --------------------------------------------------------
    # CREATE ENCODING
    # --------------------------------------------------------

    print("🧠 Creating face encoding...")

    rgb_face = cv2.cvtColor(
        face_photo,
        cv2.COLOR_BGR2RGB
    )

    encodings = face_recognition.face_encodings(
        rgb_face
    )


    if len(encodings) == 0:

        print("❌ Could not create face encoding.")
        print("Try again with better lighting.")

        return False


    # --------------------------------------------------------
    # ADD TO DATABASE
    # --------------------------------------------------------

    known_encodings.append(
        encodings[0]
    )

    known_names.append(
        name
    )


    # --------------------------------------------------------
    # SAVE DATABASE
    # --------------------------------------------------------

    save_database()


    print()
    print("==============================================")
    print("        ✅ FACE REGISTERED")
    print("==============================================")
    print(f"👤 Name: {name}")
    print(f"📸 Photo: {photo_path}")
    print(f"👥 Total registered: {len(known_names)}")
    print("==============================================")
    print()

    return True


# ============================================================
# RECOGNITION
# ============================================================

def recognize_face(frame):

    global known_encodings
    global known_names

    if len(known_encodings) == 0:

        cv2.putText(
            frame,
            "NO REGISTERED FACES",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        return


    # --------------------------------------------------------
    # Resize
    # --------------------------------------------------------

    small_frame = cv2.resize(
        frame,
        (0, 0),
        fx=SCALE,
        fy=SCALE
    )

    rgb_small = small_frame


    # --------------------------------------------------------
    # Detect faces
    # --------------------------------------------------------

    face_locations = face_recognition.face_locations(
        rgb_small
    )

    face_encodings = face_recognition.face_encodings(
        rgb_small,
        face_locations
    )


    # --------------------------------------------------------
    # Process every face
    # --------------------------------------------------------

    for face_encoding, location in zip(
        face_encodings,
        face_locations
    ):

        matches = face_recognition.compare_faces(
            known_encodings,
            face_encoding,
            tolerance=TOLERANCE
        )


        # ----------------------------------------------------
        # Find best match
        # ----------------------------------------------------

        name = "Unknown"


        if len(known_encodings) > 0:

            face_distances = face_recognition.face_distance(
                known_encodings,
                face_encoding
            )

            best_match_index = face_distances.argmin()


            if matches[best_match_index]:

                name = known_names[
                    best_match_index
                ]


        # ----------------------------------------------------
        # Coordinates
        # ----------------------------------------------------

        top, right, bottom, left = location

        top = int(top / SCALE)
        right = int(right / SCALE)
        bottom = int(bottom / SCALE)
        left = int(left / SCALE)


        # ----------------------------------------------------
        # Color
        # ----------------------------------------------------

        if name == "Unknown":

            color = (0, 0, 255)

        else:

            color = (0, 255, 0)


        # ----------------------------------------------------
        # Face box
        # ----------------------------------------------------

        cv2.rectangle(
            frame,
            (left, top),
            (right, bottom),
            color,
            2
        )


        # ----------------------------------------------------
        # Name background
        # ----------------------------------------------------

        cv2.rectangle(
            frame,
            (left, bottom - 35),
            (right, bottom),
            color,
            cv2.FILLED
        )


        # ----------------------------------------------------
        # Name
        # ----------------------------------------------------

        cv2.putText(
            frame,
            name,
            (left + 6, bottom - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )


        # ----------------------------------------------------
        # Print result
        # ----------------------------------------------------

        if name == "Unknown":

            print("🔴 UNKNOWN FACE")

        else:

            print(
                f"🟢 RECOGNIZED: {name}"
            )


# ============================================================
# MAIN CAMERA LOOP
# ============================================================

try:

    while running:

        # ----------------------------------------------------
        # Capture frame
        # ----------------------------------------------------

        frame = picam2.capture_array()


        # ====================================================
        # ENROLLMENT MODE
        # ====================================================

        if mode == "enroll":

            small_frame = cv2.resize(
                frame,
                (0, 0),
                fx=SCALE,
                fy=SCALE
            )

            face_locations = face_recognition.face_locations(
                small_frame
            )


            # ------------------------------------------------
            # No face
            # ------------------------------------------------

            if len(face_locations) == 0:

                cv2.putText(
                    frame,
                    "LOOK AT CAMERA",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
                )


                if countdown_active:

                    print(
                        "⚠️ Face lost. Countdown cancelled."
                    )

                    countdown_active = False
                    last_countdown_second = -1


            # ------------------------------------------------
            # Face detected
            # ------------------------------------------------

            else:

                primary_face = get_primary_face(
                    face_locations
                )


                top, right, bottom, left = primary_face

                top = int(top / SCALE)
                right = int(right / SCALE)
                bottom = int(bottom / SCALE)
                left = int(left / SCALE)


                # Draw primary face

                cv2.rectangle(
                    frame,
                    (left, top),
                    (right, bottom),
                    (0, 255, 0),
                    3
                )


                # ------------------------------------------------
                # Start countdown
                # ------------------------------------------------

                if not countdown_active:

                    countdown_active = True
                    countdown_start = time.time()

                    last_countdown_second = -1

                    print()
                    print("🟢 PRIMARY FACE DETECTED")
                    print("⏳ Starting 3-second countdown...")


                # ------------------------------------------------
                # Countdown
                # ------------------------------------------------

                elapsed = time.time() - countdown_start

                remaining = COUNTDOWN_SECONDS - elapsed


                if remaining > 0:

                    current_second = int(
                        remaining
                    ) + 1


                    if current_second != last_countdown_second:

                        print(
                            f"📸 {current_second}..."
                        )

                        last_countdown_second = current_second


                    cv2.putText(
                        frame,
                        str(current_second),
                        (
                            CAMERA_WIDTH // 2 - 40,
                            CAMERA_HEIGHT // 2 + 50
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        3,
                        (0, 165, 255),
                        6
                    )


                    cv2.putText(
                        frame,
                        "HOLD STILL",
                        (210, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 165, 255),
                        2
                    )


                # ------------------------------------------------
                # Capture after countdown
                # ------------------------------------------------

                else:

                    countdown_active = False

                    success = enroll_face(
                        frame,
                        primary_face
                    )


                    if success:

                        mode = "idle"

                    else:

                        mode = "idle"


                    last_countdown_second = -1


        # ====================================================
        # RECOGNITION MODE
        # ====================================================

        elif mode == "recognize":

            recognize_face(frame)


            cv2.putText(
                frame,
                "RECOGNITION MODE",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )


        # ====================================================
        # IDLE MODE
        # ====================================================

        else:

            cv2.putText(
                frame,
                "E = ENROLL    R = RECOGNIZE    Q = QUIT",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )


        # ====================================================
        # SHOW CAMERA
        # ====================================================

        cv2.imshow(
            "Raspberry Pi Face System",
            frame
        )


        # ====================================================
        # KEYBOARD INPUT
        # ====================================================

        key = cv2.waitKey(1) & 0xFF


        # ----------------------------------------------------
        # E = ENROLL
        # ----------------------------------------------------

        if key == ord("e"):

            if mode != "enroll":

                print()
                print("==============================================")
                print("              ENROLL MODE")
                print("==============================================")
                print("Look at the camera.")
                print()

                mode = "enroll"

                countdown_active = False
                last_countdown_second = -1


        # ----------------------------------------------------
        # R = RECOGNIZE
        # ----------------------------------------------------

        elif key == ord("r"):

            print()
            print("==============================================")
            print("           RECOGNITION MODE")
            print("==============================================")
            print("Looking for registered faces...")
            print("Press E to enroll.")
            print()

            mode = "recognize"

            countdown_active = False


        # ----------------------------------------------------
        # Q = QUIT
        # ----------------------------------------------------

        elif key == ord("q"):

            print()
            print("🛑 Shutting down...")
            running = False


# ============================================================
# CTRL+C
# ============================================================

except KeyboardInterrupt:

    print()
    print("🛑 Program interrupted.")


# ============================================================
# CLEANUP
# ============================================================

finally:

    print("📷 Stopping camera...")

    try:

        picam2.stop()

    except:

        pass


    cv2.destroyAllWindows()

    print("✅ Camera stopped.")
    print("👋 Program ended.")
```
