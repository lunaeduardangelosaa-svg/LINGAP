import cv2
import face_recognition
import pickle
import os
import time
from picamera2 import Picamera2

ENCODINGS_FILE = "known_face.pkl"
PHOTO_FILE = "known_face.jpg"

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

SCALE = 0.25
COUNTDOWN_SECONDS = 3
TOLERANCE = 0.5

known_encoding = None
mode = "idle"
running = True

countdown_active = False
countdown_start = 0
last_countdown_second = -1

if os.path.exists(ENCODINGS_FILE):
    try:
        with open(ENCODINGS_FILE, "rb") as f:
            data = pickle.load(f)

        if len(data.get("encodings", [])) > 0:
            known_encoding = data["encodings"][0]
            print("Registered face loaded.")
        else:
            print("No registered face found.")

    except Exception as e:
        print("Could not load registered face.")
        print(e)

else:
    print("No registered face found.")
    print("Press E to register your face.")

print("==============================================")
print("       RASPBERRY PI FACE SYSTEM")
print("==============================================")
print("E = REGISTER FACE")
print("R = RECOGNIZE FACE")
print("Q = QUIT")
print("==============================================")

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

    print("Camera ready.")

except Exception as e:
    print("Camera could not start.")
    print(e)
    exit()


def get_primary_face(face_locations):
    if not face_locations:
        return None

    def area(location):
        top, right, bottom, left = location
        return (right - left) * (bottom - top)

    return max(face_locations, key=area)


def save_face(frame, face_location):
    global known_encoding

    top, right, bottom, left = face_location

    top = int(top / SCALE)
    right = int(right / SCALE)
    bottom = int(bottom / SCALE)
    left = int(left / SCALE)

    padding = 40

    crop_top = max(0, top - padding)
    crop_bottom = min(frame.shape[0], bottom + padding)
    crop_left = max(0, left - padding)
    crop_right = min(frame.shape[1], right + padding)

    face_photo = frame[
        crop_top:crop_bottom,
        crop_left:crop_right
    ]

    if face_photo.size == 0:
        print("Could not capture face.")
        return False

    cv2.imwrite(PHOTO_FILE, face_photo)

    rgb_face = cv2.cvtColor(
        face_photo,
        cv2.COLOR_BGR2RGB
    )

    encodings = face_recognition.face_encodings(rgb_face)

    if len(encodings) == 0:
        print("Could not create face encoding.")
        return False

    known_encoding = encodings[0]

    data = {
        "encoding": known_encoding,
        "encodings": [known_encoding]
    }

    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)

    print("==============================================")
    print("FACE REGISTERED")
    print("==============================================")
    print("Your face has been saved.")
    print("==============================================")

    return True


def recognize(frame):
    if known_encoding is None:
        cv2.putText(
            frame,
            "NO FACE REGISTERED",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )
        return

    small_frame = cv2.resize(
        frame,
        (0, 0),
        fx=SCALE,
        fy=SCALE
    )

    face_locations = face_recognition.face_locations(
        small_frame
    )

    face_encodings = face_recognition.face_encodings(
        small_frame,
        face_locations
    )

    for face_encoding, location in zip(
        face_encodings,
        face_locations
    ):
        distance = face_recognition.face_distance(
            [known_encoding],
            face_encoding
        )[0]

        match = distance <= TOLERANCE

        top, right, bottom, left = location

        top = int(top / SCALE)
        right = int(right / SCALE)
        bottom = int(bottom / SCALE)
        left = int(left / SCALE)

        if match:
            label = "KNOWN FACE"
            color = (0, 255, 0)
        else:
            label = "UNKNOWN"
            color = (0, 0, 255)

        cv2.rectangle(
            frame,
            (left, top),
            (right, bottom),
            color,
            3
        )

        cv2.rectangle(
            frame,
            (left, bottom - 40),
            (right, bottom),
            color,
            cv2.FILLED
        )

        cv2.putText(
            frame,
            label,
            (left + 5, bottom - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


try:
    while running:

        frame = picam2.capture_array()

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
                    countdown_active = False
                    last_countdown_second = -1
                    print("Face lost. Countdown cancelled.")

            else:

                primary_face = get_primary_face(
                    face_locations
                )

                top, right, bottom, left = primary_face

                display_top = int(top / SCALE)
                display_right = int(right / SCALE)
                display_bottom = int(bottom / SCALE)
                display_left = int(left / SCALE)

                cv2.rectangle(
                    frame,
                    (display_left, display_top),
                    (display_right, display_bottom),
                    (0, 255, 0),
                    3
                )

                if not countdown_active:

                    countdown_active = True
                    countdown_start = time.time()
                    last_countdown_second = -1

                    print("Face detected.")
                    print("Hold still.")

                elapsed = time.time() - countdown_start
                remaining = COUNTDOWN_SECONDS - elapsed

                if remaining > 0:

                    current_second = int(remaining) + 1

                    if current_second != last_countdown_second:

                        print(current_second)
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

                else:

                    countdown_active = False
                    last_countdown_second = -1

                    if save_face(frame, primary_face):
                        mode = "idle"

        elif mode == "recognize":

            recognize(frame)

            cv2.putText(
                frame,
                "RECOGNITION",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

        else:

            cv2.putText(
                frame,
                "E REGISTER   R RECOGNIZE   Q QUIT",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )

        cv2.imshow(
            "Raspberry Pi Face System",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        if key == ord("e"):

            print("Registration mode.")

            mode = "enroll"
            countdown_active = False
            last_countdown_second = -1

        elif key == ord("r"):

            print("Recognition mode.")

            mode = "recognize"
            countdown_active = False

        elif key == ord("q"):

            running = False

except KeyboardInterrupt:
    pass

finally:

    try:
        picam2.stop()
    except:
        pass

    cv2.destroyAllWindows()

    print("System stopped.")
