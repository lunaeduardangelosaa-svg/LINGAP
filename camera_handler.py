import cv2
import face_recognition
import pickle
import os
import time
import numpy as np

from picamera2 import Picamera2


# ============================================
# FILES
# ============================================

PEOPLE_FILE = "people.pkl"

# Old file from your previous system
OLD_ENCODINGS_FILE = "known_face.pkl"


# ============================================
# CAMERA
# ============================================

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480


# ============================================
# FACE RECOGNITION
# ============================================

SCALE = 0.25
TOLERANCE = 0.5


# ============================================
# ENROLLMENT
# ============================================

COUNTDOWN_SECONDS = 3


class CameraHandler:

    def __init__(self):

        self.camera = None

        self.running = False

        self.mode = "idle"

        # ----------------------------------------
        # PEOPLE
        #
        # [
        #   {
        #       "id": 1,
        #       "name": "Juan",
        #       "encoding": ...
        #   }
        # ]
        # ----------------------------------------

        self.people = []

        # ----------------------------------------
        # COUNTDOWN
        # ----------------------------------------

        self.countdown_active = False
        self.countdown_start = 0
        self.last_countdown_second = -1

        # ----------------------------------------
        # LOAD PEOPLE
        # ----------------------------------------

        self.load_people()


    # ============================================
    # LOAD PEOPLE
    # ============================================

    def load_people(self):

        self.people = []

        # ----------------------------------------
        # NEW PEOPLE FILE
        # ----------------------------------------

        if os.path.exists(PEOPLE_FILE):

            try:

                with open(
                    PEOPLE_FILE,
                    "rb"
                ) as f:

                    data = pickle.load(f)

                self.people = data.get(
                    "people",
                    []
                )

                print(
                    "Loaded",
                    len(self.people),
                    "registered person(s)."
                )

                return

            except Exception as error:

                print(
                    "Error loading people.pkl:",
                    error
                )


        # ----------------------------------------
        # IMPORT OLD KNOWN_FACE.PKL
        # ----------------------------------------

        if os.path.exists(OLD_ENCODINGS_FILE):

            try:

                with open(
                    OLD_ENCODINGS_FILE,
                    "rb"
                ) as f:

                    data = pickle.load(f)

                old_encodings = data.get(
                    "encodings",
                    []
                )

                for index, encoding in enumerate(
                    old_encodings,
                    start=1
                ):

                    self.people.append(
                        {
                            "id": index,
                            "name": "Person " + str(index),
                            "encoding": encoding
                        }
                    )

                if self.people:

                    self.save_people()

                    print(
                        "Imported",
                        len(self.people),
                        "old face(s)."
                    )

                    print(
                        "They are currently named Person 1, "
                        "Person 2, etc."
                    )

            except Exception as error:

                print(
                    "Error importing old faces:",
                    error
                )


    # ============================================
    # SAVE PEOPLE
    # ============================================

    def save_people(self):

        with open(
            PEOPLE_FILE,
            "wb"
        ) as f:

            pickle.dump(
                {
                    "people": self.people
                },
                f
            )


    # ============================================
    # GET PEOPLE
    # ============================================

    def get_people(self):

        return self.people


    # ============================================
    # GET PERSON BY ID
    # ============================================

    def get_person(
        self,
        person_id
    ):

        for person in self.people:

            if person["id"] == person_id:

                return person

        return None


    # ============================================
    # START CAMERA
    # ============================================

    def start(self):

        if self.camera is not None:

            return

        self.camera = Picamera2()

        config = (
            self.camera.create_preview_configuration(

                main={
                    "size": (
                        CAMERA_WIDTH,
                        CAMERA_HEIGHT
                    ),

                    "format": "RGB888"
                }
            )
        )

        self.camera.configure(
            config
        )

        self.camera.start()

        time.sleep(2)

        self.running = True


    # ============================================
    # CAPTURE
    # ============================================

    def capture(self):

        if self.camera is None:

            return None

        return self.camera.capture_array()


    # ============================================
    # GET FACES
    # ============================================

    def get_faces(
        self,
        frame
    ):

        small = cv2.resize(

            frame,

            (0, 0),

            fx=SCALE,
            fy=SCALE
        )

        locations = (
            face_recognition.face_locations(
                small
            )
        )

        return small, locations


    # ============================================
    # PRIMARY FACE
    # ============================================

    def get_primary_face(
        self,
        locations
    ):

        if not locations:

            return None

        return max(

            locations,

            key=lambda x:
            (x[1] - x[3]) *
            (x[2] - x[0])
        )


    # ============================================
    # ENROLL
    # ============================================

    def enroll(
        self,
        frame
    ):

        small, locations = (
            self.get_faces(frame)
        )

        # ----------------------------------------
        # NO FACE
        # ----------------------------------------

        if not locations:

            self.countdown_active = False

            self.last_countdown_second = -1

            cv2.putText(

                frame,

                "NO FACE",

                (20, 40),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (0, 0, 255),

                2
            )

            return (
                frame,
                False,
                "NO FACE"
            )


        # ----------------------------------------
        # PRIMARY FACE
        # ----------------------------------------

        primary = (
            self.get_primary_face(
                locations
            )
        )

        top, right, bottom, left = primary


        # Convert small coordinates
        # back to full camera size.

        top = int(top / SCALE)
        right = int(right / SCALE)
        bottom = int(bottom / SCALE)
        left = int(left / SCALE)


        # ----------------------------------------
        # DRAW BOX
        # ----------------------------------------

        cv2.rectangle(

            frame,

            (left, top),

            (right, bottom),

            (0, 255, 0),

            3
        )


        # ----------------------------------------
        # START COUNTDOWN
        # ----------------------------------------

        if not self.countdown_active:

            self.countdown_active = True

            self.countdown_start = time.time()

            self.last_countdown_second = -1


        elapsed = (
            time.time() -
            self.countdown_start
        )

        remaining = (
            COUNTDOWN_SECONDS -
            elapsed
        )


        # ----------------------------------------
        # COUNTDOWN
        # ----------------------------------------

        if remaining > 0:

            second = (
                int(remaining) + 1
            )

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

            return (
                frame,
                False,
                "COUNTDOWN"
            )


        # ----------------------------------------
        # RESET COUNTDOWN
        # ----------------------------------------

        self.countdown_active = False

        self.last_countdown_second = -1


        # ----------------------------------------
        # CROP FACE
        # ----------------------------------------

        padding = 40

        crop_top = max(
            0,
            top - padding
        )

        crop_bottom = min(
            frame.shape[0],
            bottom + padding
        )

        crop_left = max(
            0,
            left - padding
        )

        crop_right = min(
            frame.shape[1],
            right + padding
        )

        face = frame[
            crop_top:crop_bottom,
            crop_left:crop_right
        ]


        if face.size == 0:

            return (
                frame,
                False,
                "CAPTURE FAILED"
            )


        # ----------------------------------------
        # FACE ENCODING
        # ----------------------------------------

        # Picamera2 gives RGB.
        # face_recognition expects RGB.

        rgb = face.copy()

        encodings = (
            face_recognition.face_encodings(
                rgb
            )
        )


        if not encodings:

            return (
                frame,
                False,
                "ENCODING FAILED"
            )


        new_encoding = encodings[0]


        # ----------------------------------------
        # ASK FOR PERSON NAME
        # ----------------------------------------

        print()
        print(
            "================================"
        )
        print(
            "NEW FACE DETECTED"
        )
        print(
            "================================"
        )

        name = input(
            "Enter person's name: "
        ).strip()


        if not name:

            name = "Person"


        # ----------------------------------------
        # NEW ID
        # ----------------------------------------

        if self.people:

            new_id = max(
                person["id"]
                for person in self.people
            ) + 1

        else:

            new_id = 1


        # ----------------------------------------
        # SAVE PERSON
        # ----------------------------------------

        person = {

            "id": new_id,

            "name": name,

            "encoding": new_encoding
        }


        self.people.append(
            person
        )


        self.save_people()


        # ----------------------------------------
        # SAVE PHOTO
        # ----------------------------------------

        photo_file = (
            "person_"
            + str(new_id)
            + ".jpg"
        )

        # Convert RGB → BGR for OpenCV.

        photo_bgr = cv2.cvtColor(

            face,

            cv2.COLOR_RGB2BGR
        )

        cv2.imwrite(

            photo_file,

            photo_bgr
        )


        self.mode = "idle"


        print()
        print(
            "================================"
        )
        print(
            "FACE REGISTERED"
        )
        print(
            "ID:",
            new_id
        )
        print(
            "NAME:",
            name
        )
        print(
            "================================"
        )
        print()


        return (
            frame,
            True,
            "FACE REGISTERED"
        )


    # ============================================
    # RECOGNIZE
    # ============================================

    def recognize(
        self,
        frame
    ):

        # ----------------------------------------
        # NO PEOPLE
        # ----------------------------------------

        if not self.people:

            cv2.putText(

                frame,

                "NO PEOPLE REGISTERED",

                (20, 40),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (0, 0, 255),

                2
            )

            return (
                frame,
                None
            )


        # ----------------------------------------
        # FIND FACES
        # ----------------------------------------

        small, locations = (
            self.get_faces(frame)
        )


        encodings = (
            face_recognition.face_encodings(

                small,

                locations
            )
        )


        best_person = None


        # ----------------------------------------
        # CHECK EVERY CAMERA FACE
        # ----------------------------------------

        for encoding, location in zip(

            encodings,

            locations
        ):

            known_encodings = [

                person["encoding"]

                for person in self.people
            ]


            distances = (
                face_recognition.face_distance(

                    known_encodings,

                    encoding
                )
            )


            if len(distances) == 0:

                continue


            best_index = int(
                np.argmin(distances)
            )


            best_distance = float(
                distances[best_index]
            )


            match = (
                best_distance <= TOLERANCE
            )


            # ------------------------------------
            # FACE LOCATION
            # ------------------------------------

            top, right, bottom, left = (
                location
            )

            top = int(top / SCALE)
            right = int(right / SCALE)
            bottom = int(bottom / SCALE)
            left = int(left / SCALE)


            # ------------------------------------
            # MATCH
            # ------------------------------------

            if match:

                person = (
                    self.people[best_index]
                )

                label = (
                    person["name"]
                )

                color = (
                    0,
                    255,
                    0
                )

                best_person = person


            else:

                label = "UNKNOWN"

                color = (
                    0,
                    0,
                    255
                )


            # ------------------------------------
            # FACE BOX
            # ------------------------------------

            cv2.rectangle(

                frame,

                (left, top),

                (right, bottom),

                color,

                3
            )


            # ------------------------------------
            # LABEL BACKGROUND
            # ------------------------------------

            cv2.rectangle(

                frame,

                (
                    left,
                    max(0, bottom - 45)
                ),

                (
                    right,
                    bottom
                ),

                color,

                cv2.FILLED
            )


            # ------------------------------------
            # LABEL
            # ------------------------------------

            cv2.putText(

                frame,

                label,

                (
                    left + 5,
                    bottom - 12
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.65,

                (255, 255, 255),

                2
            )


        return (
            frame,
            best_person
        )


    # ============================================
    # SET MODE
    # ============================================

    def set_mode(
        self,
        mode
    ):

        self.mode = mode


        if mode != "enroll":

            self.countdown_active = False

            self.last_countdown_second = -1


    # ============================================
    # CLEAR ALL PEOPLE
    # ============================================

    def clear_people(self):

        self.people = []

        if os.path.exists(
            PEOPLE_FILE
        ):

            os.remove(
                PEOPLE_FILE
            )

        print(
            "All registered people deleted."
        )


    # ============================================
    # STOP
    # ============================================

    def stop(self):

        self.running = False


        if self.camera is not None:

            self.camera.stop()

            self.camera = None


        cv2.destroyAllWindows()
