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
TOLERANCE = 0.5
COUNTDOWN_SECONDS = 3


class CameraHandler:

    def __init__(self):
        self.camera = None
        self.known_encoding = None
        self.running = False
        self.mode = "idle"

        self.countdown_active = False
        self.countdown_start = 0
        self.last_countdown_second = -1

        self.load_face()

    def load_face(self):
        if not os.path.exists(ENCODINGS_FILE):
            return

        try:
            with open(ENCODINGS_FILE, "rb") as f:
                data = pickle.load(f)

            encodings = data.get("encodings", [])

            if encodings:
                self.known_encoding = encodings[0]

        except Exception:
            self.known_encoding = None

    def start(self):
        if self.camera is not None:
            return

        self.camera = Picamera2()

        config = self.camera.create_preview_configuration(
            main={
                "size": (CAMERA_WIDTH, CAMERA_HEIGHT),
                "format": "RGB888"
            }
        )

        self.camera.configure(config)
        self.camera.start()

        time.sleep(2)

        self.running = True

    def capture(self):
        if self.camera is None:
            return None

        return self.camera.capture_array()

    def get_faces(self, frame):
        small = cv2.resize(
            frame,
            (0, 0),
            fx=SCALE,
            fy=SCALE
        )

        locations = face_recognition.face_locations(
            small
        )

        return small, locations

    def get_primary_face(self, locations):
        if not locations:
            return None

        return max(
            locations,
            key=lambda x: (x[1] - x[3]) * (x[2] - x[0])
        )

    def enroll(self, frame):
        small, locations = self.get_faces(frame)

        if not locations:
            self.countdown_active = False
            self.last_countdown_second = -1

            return frame, False, "NO FACE"

        primary = self.get_primary_face(locations)

        top, right, bottom, left = primary

        top = int(top / SCALE)
        right = int(right / SCALE)
        bottom = int(bottom / SCALE)
        left = int(left / SCALE)

        cv2.rectangle(
            frame,
            (left, top),
            (right, bottom),
            (0, 255, 0),
            3
        )

        if not self.countdown_active:
            self.countdown_active = True
            self.countdown_start = time.time()
            self.last_countdown_second = -1

        elapsed = time.time() - self.countdown_start
        remaining = COUNTDOWN_SECONDS - elapsed

        if remaining > 0:

            second = int(remaining) + 1

            cv2.putText(
                frame,
                str(second),
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

            return frame, False, "COUNTDOWN"

        self.countdown_active = False
        self.last_countdown_second = -1

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

        face = frame[
            crop_top:crop_bottom,
            crop_left:crop_right
        ]

        if face.size == 0:
            return frame, False, "CAPTURE FAILED"

        cv2.imwrite(
            PHOTO_FILE,
            face
        )

        rgb = cv2.cvtColor(
            face,
            cv2.COLOR_BGR2RGB
        )

        encodings = face_recognition.face_encodings(rgb)

        if not encodings:
            return frame, False, "ENCODING FAILED"

        self.known_encoding = encodings[0]

        with open(ENCODINGS_FILE, "wb") as f:
            pickle.dump(
                {
                    "encodings": [self.known_encoding]
                },
                f
            )

        self.mode = "idle"

        return frame, True, "FACE REGISTERED"

    def recognize(self, frame):
        if self.known_encoding is None:

            cv2.putText(
                frame,
                "NO FACE REGISTERED",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

            return frame, None

        small, locations = self.get_faces(frame)

        encodings = face_recognition.face_encodings(
            small,
            locations
        )

        result = None

        for encoding, location in zip(
            encodings,
            locations
        ):

            distance = face_recognition.face_distance(
                [self.known_encoding],
                encoding
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
                result = True
            else:
                label = "UNKNOWN"
                color = (0, 0, 255)
                result = False

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

        return frame, result

    def set_mode(self, mode):
        self.mode = mode

        if mode != "enroll":
            self.countdown_active = False
            self.last_countdown_second = -1

    def stop(self):
        self.running = False

        if self.camera is not None:
            self.camera.stop()
            self.camera = None

        cv2.destroyAllWindows()
