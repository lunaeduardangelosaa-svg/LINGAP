import cv2
import face_recognition
import pickle
import os
import time
import numpy as np
import serial
import subprocess

from picamera2 import Picamera2


# ============================================================
# FILES
# ============================================================

PEOPLE_FILE = "people.pkl"
OLD_ENCODINGS_FILE = "known_face.pkl"


# ============================================================
# CAMERA
# ============================================================

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

SCALE = 0.25
TOLERANCE = 0.5

COUNTDOWN_SECONDS = 3


# ============================================================
# BLUETOOTH
# ============================================================
#
# HC-05 is connected to:
#
# Physical Pin 27 = GPIO0 = TXD2
# Physical Pin 28 = GPIO1 = RXD2
#
# Pi Pin 27 TX  -> HC-05 RX
# Pi Pin 28 RX  <- HC-05 TX
#
# UART device:
#
# /dev/ttyAMA2
#
# DO NOT use /dev/serial0 here because the AS608
# is using /dev/serial0.
#
# ============================================================

BLUETOOTH_PORT = "/dev/ttyAMA2"
BLUETOOTH_BAUD = 9600


# ============================================================
# RECOGNITION
# ============================================================

RECOGNITION_COOLDOWN = 2


class CameraHandler:

    def __init__(self):

        # ====================================================
        # CAMERA STATE
        # ====================================================

        self.camera = None

        self.running = False

        self.mode = "idle"


        # ====================================================
        # PEOPLE
        # ====================================================

        self.people = []


        # ====================================================
        # FACE ENROLLMENT
        # ====================================================

        self.countdown_active = False

        self.countdown_start = 0

        self.last_countdown_second = -1


        # ====================================================
        # FACE RECOGNITION
        # ====================================================

        self.last_recognition_time = 0

        self.recognition_locked = False


        # ====================================================
        # BLUETOOTH
        # ====================================================

        self.bluetooth = None


        # ====================================================
        # LOAD PEOPLE
        # ====================================================

        self.load_people()


        # ====================================================
        # OPEN BLUETOOTH
        # ====================================================

        self.connect_bluetooth()


    # ========================================================
    # TEXT TO SPEECH
    # ========================================================

    def speak(
        self,
        text
    ):

        try:

            subprocess.Popen(
                [
                    "espeak-ng",
                    "-v",
                    "en",
                    "-s",
                    "145",
                    "-p",
                    "45",
                    "-a",
                    "150",
                    text
                ],

                stdout=subprocess.DEVNULL,

                stderr=subprocess.DEVNULL
            )

        except Exception as error:

            print(
                "VOICE ERROR:",
                error
            )


    # ========================================================
    # CONNECT BLUETOOTH
    # ========================================================

    def connect_bluetooth(self):

        print()
        print("=" * 50)
        print("     HC-05 BLUETOOTH UART")
        print("=" * 50)

        print(
            "Port:",
            BLUETOOTH_PORT
        )

        print(
            "Baud:",
            BLUETOOTH_BAUD
        )

        print(
            "GPIO0 / Pin 27 = TXD2"
        )

        print(
            "GPIO1 / Pin 28 = RXD2"
        )

        print("=" * 50)

        try:

            self.bluetooth = serial.Serial(

                port=BLUETOOTH_PORT,

                baudrate=BLUETOOTH_BAUD,

                timeout=1,

                write_timeout=2
            )


            time.sleep(
                1
            )


            self.bluetooth.reset_input_buffer()

            self.bluetooth.reset_output_buffer()


            print(
                "HC-05 UART CONNECTED."
            )

            print("=" * 50)
            print()


            return True


        except Exception as error:

            self.bluetooth = None


            print()
            print("=" * 50)
            print(" HC-05 UART CONNECTION FAILED")
            print("=" * 50)

            print(
                "Error type:",
                type(error).__name__
            )

            print(
                "Error:",
                error
            )

            print()
            print(
                "Expected UART:",
                BLUETOOTH_PORT
            )

            print(
                "Expected baud:",
                BLUETOOTH_BAUD
            )

            print()
            print(
                "HC-05 wiring:"
            )

            print(
                "Pi Pin 27 / GPIO0 / TXD2 -> HC-05 RX"
            )

            print(
                "Pi Pin 28 / GPIO1 / RXD2 -> HC-05 TX"
            )

            print("=" * 50)
            print()


            return False


    # ========================================================
    # BLUETOOTH SEND
    # ========================================================

    def send_bluetooth(
        self,
        message
    ):

        try:

            # ------------------------------------------------
            # CHECK CONNECTION
            # ------------------------------------------------

            if self.bluetooth is None:

                print(
                    "Bluetooth not connected."
                )

                print(
                    "Attempting reconnect..."
                )

                if not self.connect_bluetooth():

                    return False


            # ------------------------------------------------
            # CLEAN MESSAGE
            # ------------------------------------------------

            message = str(
                message
            ).strip()


            # ------------------------------------------------
            # ASCII + NEWLINE
            # ------------------------------------------------

            data = (

                message
                + "\n"

            ).encode(

                "ascii",

                errors="replace"
            )


            # ------------------------------------------------
            # DEBUG
            # ------------------------------------------------

            print()
            print("=" * 50)
            print("BLUETOOTH SEND")
            print("=" * 50)

            print(
                "MESSAGE:",
                repr(message)
            )

            print(
                "BYTES:",
                repr(data)
            )

            print(
                "PORT:",
                BLUETOOTH_PORT
            )

            print(
                "BAUD:",
                BLUETOOTH_BAUD
            )

            print("=" * 50)


            # ------------------------------------------------
            # SEND
            # ------------------------------------------------

            self.bluetooth.write(
                data
            )

            self.bluetooth.flush()


            # ------------------------------------------------
            # DEBUG
            # ------------------------------------------------

            print(
                "SENT:",
                repr(data)
            )

            print("=" * 50)
            print()


            return True


        except Exception as error:

            print()
            print("=" * 50)
            print("BLUETOOTH SEND ERROR")
            print("=" * 50)

            print(
                "Error type:",
                type(error).__name__
            )

            print(
                "Error:",
                error
            )

            print("=" * 50)
            print()


            # ------------------------------------------------
            # TRY RECONNECT
            # ------------------------------------------------

            try:

                if self.bluetooth is not None:

                    self.bluetooth.close()

            except Exception:

                pass


            self.bluetooth = None


            return False


    # ========================================================
    # LOAD PEOPLE
    # ========================================================

    def load_people(self):

        self.people = []


        # ----------------------------------------------------
        # NEW PEOPLE FILE
        # ----------------------------------------------------

        if os.path.exists(
            PEOPLE_FILE
        ):

            try:

                with open(
                    PEOPLE_FILE,
                    "rb"
                ) as f:

                    data = pickle.load(
                        f
                    )


                self.people = data.get(
                    "people",
                    []
                )


                print(
                    "Loaded",
                    len(
                        self.people
                    ),
                    "registered person(s)."
                )


                return


            except Exception as error:

                print(
                    "Error loading people.pkl:",
                    error
                )


        # ----------------------------------------------------
        # OLD ENCODINGS FILE
        # ----------------------------------------------------

        if os.path.exists(
            OLD_ENCODINGS_FILE
        ):

            try:

                with open(
                    OLD_ENCODINGS_FILE,
                    "rb"
                ) as f:

                    data = pickle.load(
                        f
                    )


                old_encodings = data.get(
                    "encodings",
                    []
                )


                for index, encoding in enumerate(
                    old_encodings,
                    start=1
                ):

                    self.people.append({

                        "id":
                            index,

                        "name":
                            "Person "
                            + str(index),

                        "encoding":
                            encoding
                    })


                if self.people:

                    self.save_people()


                    print(
                        "Imported",
                        len(
                            self.people
                        ),
                        "old face(s)."
                    )


            except Exception as error:

                print(
                    "Error importing old faces:",
                    error
                )


    # ========================================================
    # SAVE PEOPLE
    # ========================================================

    def save_people(self):

        with open(
            PEOPLE_FILE,
            "wb"
        ) as f:

            pickle.dump(

                {
                    "people":
                        self.people
                },

                f
            )


    # ========================================================
    # GET PEOPLE
    # ========================================================

    def get_people(self):

        return self.people


    # ========================================================
    # GET PERSON
    # ========================================================

    def get_person(
        self,
        person_id
    ):

        for person in self.people:

            if int(
                person["id"]
            ) == int(
                person_id
            ):

                return person


        return None


    # ========================================================
    # START CAMERA
    # ========================================================

    def start(self):

        if self.camera is not None:

            return


        self.camera = Picamera2()


        config = (

            self.camera
            .create_preview_configuration(

                main={

                    "size": (

                        CAMERA_WIDTH,

                        CAMERA_HEIGHT
                    ),

                    "format":
                        "RGB888"
                }
            )
        )


        self.camera.configure(
            config
        )


        self.camera.start()


        time.sleep(
            2
        )


        self.running = True


    # ========================================================
    # CAPTURE
    # ========================================================

    def capture(self):

        if self.camera is None:

            return None


        return (

            self.camera
            .capture_array()
        )


    # ========================================================
    # GET FACES
    # ========================================================

    def get_faces(
        self,
        frame
    ):

        small = cv2.resize(

            frame,

            (
                0,
                0
            ),

            fx=SCALE,

            fy=SCALE
        )


        locations = (

            face_recognition
            .face_locations(
                small
            )
        )


        return (

            small,

            locations
        )


    # ========================================================
    # PRIMARY FACE
    # ========================================================

    def get_primary_face(
        self,
        locations
    ):

        if not locations:

            return None


        return max(

            locations,

            key=lambda x:

                (x[1] - x[3])
                *
                (x[2] - x[0])
        )


    # ========================================================
    # FACE ENROLLMENT
    # ========================================================

    def enroll(
        self,
        frame
    ):

        small, locations = (

            self.get_faces(
                frame
            )
        )


        # ----------------------------------------------------
        # NO FACE
        # ----------------------------------------------------

        if not locations:

            self.countdown_active = False

            self.last_countdown_second = -1


            cv2.putText(

                frame,

                "NO FACE",

                (
                    20,
                    40
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (
                    0,
                    0,
                    255
                ),

                2
            )


            return (

                frame,

                False,

                "NO FACE"
            )


        # ----------------------------------------------------
        # PRIMARY FACE
        # ----------------------------------------------------

        primary = (

            self.get_primary_face(
                locations
            )
        )


        top, right, bottom, left = primary


        top = int(
            top / SCALE
        )

        right = int(
            right / SCALE
        )

        bottom = int(
            bottom / SCALE
        )

        left = int(
            left / SCALE
        )


        # ----------------------------------------------------
        # DRAW FACE
        # ----------------------------------------------------

        cv2.rectangle(

            frame,

            (
                left,
                top
            ),

            (
                right,
                bottom
            ),

            (
                0,
                255,
                0
            ),

            3
        )


        # ----------------------------------------------------
        # START COUNTDOWN
        # ----------------------------------------------------

        if not self.countdown_active:

            self.countdown_active = True

            self.countdown_start = (
                time.time()
            )

            self.last_countdown_second = -1


            self.speak(
                "Registering face. Please hold still."
            )


        # ----------------------------------------------------
        # COUNTDOWN
        # ----------------------------------------------------

        elapsed = (

            time.time()
            -
            self.countdown_start
        )


        remaining = (

            COUNTDOWN_SECONDS
            -
            elapsed
        )


        if remaining > 0:

            second = (

                int(
                    remaining
                )
                + 1
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

                (
                    0,
                    165,
                    255
                ),

                6
            )


            cv2.putText(

                frame,

                "HOLD STILL",

                (
                    210,
                    60
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (
                    0,
                    165,
                    255
                ),

                2
            )


            return (

                frame,

                False,

                "COUNTDOWN"
            )


        # ----------------------------------------------------
        # RESET COUNTDOWN
        # ----------------------------------------------------

        self.countdown_active = False

        self.last_countdown_second = -1


        # ----------------------------------------------------
        # FACE CROP
        # ----------------------------------------------------

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

            crop_top:
            crop_bottom,

            crop_left:
            crop_right
        ]


        if face.size == 0:

            return (

                frame,

                False,

                "CAPTURE FAILED"
            )


        # ----------------------------------------------------
        # ENCODE FACE
        # ----------------------------------------------------

        rgb = face.copy()


        encodings = (

            face_recognition
            .face_encodings(
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


        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        print()
        print("=" * 50)
        print("NEW FACE DETECTED")
        print("=" * 50)


        name = input(
            "Enter person's name: "
        ).strip()


        if not name:

            name = "Person"


        # ----------------------------------------------------
        # NEW ID
        # ----------------------------------------------------

        if self.people:

            new_id = (

                max(

                    int(
                        person["id"]
                    )

                    for person
                    in self.people
                )

                + 1
            )

        else:

            new_id = 1


        # ----------------------------------------------------
        # PERSON OBJECT
        # ----------------------------------------------------

        person = {

            "id":
                new_id,

            "name":
                name,

            "encoding":
                new_encoding
        }


        self.people.append(
            person
        )


        self.save_people()


        # ----------------------------------------------------
        # SAVE PHOTO
        # ----------------------------------------------------

        photo_file = (

            "person_"
            + str(new_id)
            + ".jpg"
        )


        photo_bgr = cv2.cvtColor(

            face,

            cv2.COLOR_RGB2BGR
        )


        cv2.imwrite(

            photo_file,

            photo_bgr
        )


        # ----------------------------------------------------
        # BLUETOOTH ENROLL
        # ----------------------------------------------------

        message = (

            "ENROLL|"
            + str(new_id)
            + "|"
            + name
        )


        print()
        print("=" * 50)
        print("ENROLLMENT")
        print("=" * 50)

        print(
            "ID:",
            new_id
        )

        print(
            "NAME:",
            name
        )

        print(
            "MESSAGE:",
            repr(message)
        )

        print("=" * 50)


        bluetooth_success = (

            self.send_bluetooth(
                message
            )
        )


        # ----------------------------------------------------
        # VOICE
        # ----------------------------------------------------

        self.speak(

            "Successfully enrolled, "
            + name
        )


        # ----------------------------------------------------
        # FINAL OUTPUT
        # ----------------------------------------------------

        print()
        print("=" * 50)
        print("FACE REGISTERED")
        print("=" * 50)

        print(
            "ID:",
            new_id
        )

        print(
            "NAME:",
            name
        )

        print(
            "SENT:",
            message
        )

        print(
            "BLUETOOTH:",
            bluetooth_success
        )

        print("=" * 50)
        print()


        # ----------------------------------------------------
        # RETURN TO IDLE
        # ----------------------------------------------------

        self.mode = "idle"

        self.recognition_locked = False


        return (

            frame,

            True,

            "FACE REGISTERED"
        )


    # ========================================================
    # FACE RECOGNITION
    # ========================================================

    def recognize(
        self,
        frame
    ):

        # ----------------------------------------------------
        # LOCK
        # ----------------------------------------------------

        if self.recognition_locked:

            return (

                frame,

                None
            )


        # ----------------------------------------------------
        # NO PEOPLE
        # ----------------------------------------------------

        if not self.people:

            cv2.putText(

                frame,

                "NO PEOPLE REGISTERED",

                (
                    20,
                    40
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (
                    0,
                    0,
                    255
                ),

                2
            )


            return (

                frame,

                None
            )


        # ----------------------------------------------------
        # FIND FACES
        # ----------------------------------------------------

        small, locations = (

            self.get_faces(
                frame
            )
        )


        encodings = (

            face_recognition
            .face_encodings(

                small,

                locations
            )
        )


        best_person = None


        # ----------------------------------------------------
        # PROCESS EACH FACE
        # ----------------------------------------------------

        for encoding, location in zip(

            encodings,

            locations
        ):

            known_encodings = [

                person["encoding"]

                for person
                in self.people
            ]


            distances = (

                face_recognition
                .face_distance(

                    known_encodings,

                    encoding
                )
            )


            if len(
                distances
            ) == 0:

                continue


            best_index = int(

                np.argmin(
                    distances
                )
            )


            best_distance = float(

                distances[
                    best_index
                ]
            )


            match = (

                best_distance
                <=
                TOLERANCE
            )


            top, right, bottom, left = (
                location
            )


            top = int(
                top / SCALE
            )

            right = int(
                right / SCALE
            )

            bottom = int(
                bottom / SCALE
            )

            left = int(
                left / SCALE
            )


            # ------------------------------------------------
            # MATCH
            # ------------------------------------------------

            if match:

                person = (

                    self.people[
                        best_index
                    ]
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


                current_time = (
                    time.time()
                )


                if (

                    current_time
                    -
                    self.last_recognition_time

                    >=

                    RECOGNITION_COOLDOWN
                ):

                    person_id = int(
                        person["id"]
                    )


                    person_name = str(
                        person["name"]
                    )


                    # ----------------------------------------
                    # LOGIN MESSAGE
                    # ----------------------------------------

                    message = (

                        "LOGIN|"
                        + str(person_id)
                        + "|"
                        + person_name
                    )


                    print()
                    print("=" * 50)
                    print("FACE RECOGNIZED")
                    print("=" * 50)

                    print(
                        "ID:",
                        person_id
                    )

                    print(
                        "NAME:",
                        person_name
                    )

                    print(
                        "MESSAGE:",
                        repr(message)
                    )

                    print("=" * 50)


                    # ----------------------------------------
                    # SEND BLUETOOTH
                    # ----------------------------------------

                    bluetooth_success = (

                        self.send_bluetooth(
                            message
                        )
                    )


                    # ----------------------------------------
                    # VOICE
                    # ----------------------------------------

                    self.speak(

                        person_name
                        + ", logging in."
                    )


                    self.last_recognition_time = (
                        current_time
                    )


                    # ----------------------------------------
                    # LOCK RECOGNITION
                    # ----------------------------------------

                    self.recognition_locked = True

                    self.mode = "idle"


                    print(
                        "BLUETOOTH:",
                        bluetooth_success
                    )


            # ------------------------------------------------
            # UNKNOWN
            # ------------------------------------------------

            else:

                label = "UNKNOWN"

                color = (

                    0,
                    0,
                    255
                )


            # ------------------------------------------------
            # DRAW FACE
            # ------------------------------------------------

            cv2.rectangle(

                frame,

                (
                    left,
                    top
                ),

                (
                    right,
                    bottom
                ),

                color,

                3
            )


            # ------------------------------------------------
            # LABEL BACKGROUND
            # ------------------------------------------------

            cv2.rectangle(

                frame,

                (
                    left,

                    max(
                        0,
                        bottom - 45
                    )
                ),

                (
                    right,

                    bottom
                ),

                color,

                cv2.FILLED
            )


            # ------------------------------------------------
            # LABEL
            # ------------------------------------------------

            cv2.putText(

                frame,

                label,

                (
                    left + 5,

                    bottom - 12
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.65,

                (
                    255,
                    255,
                    255
                ),

                2
            )


        return (

            frame,

            best_person
        )


    # ========================================================
    # SET MODE
    # ========================================================

    def set_mode(
        self,
        mode
    ):

        self.mode = mode


        if mode == "recognize":

            self.recognition_locked = False

            self.last_recognition_time = (

                time.time()
                -
                RECOGNITION_COOLDOWN
            )


        if mode != "enroll":

            self.countdown_active = False

            self.last_countdown_second = -1


    # ========================================================
    # DELETE PERSON
    # ========================================================

    def delete_person(
        self,
        person_id
    ):

        self.people = [

            person

            for person
            in self.people

            if int(
                person["id"]
            )
            != int(
                person_id
            )
        ]


        self.save_people()


        # ----------------------------------------------------
        # DELETE PHOTO
        # ----------------------------------------------------

        photo_file = (

            "person_"
            + str(person_id)
            + ".jpg"
        )


        if os.path.exists(
            photo_file
        ):

            os.remove(
                photo_file
            )


        # ----------------------------------------------------
        # BLUETOOTH
        # ----------------------------------------------------

        self.send_bluetooth(

            "DELETE|"
            + str(person_id)
        )


        print(

            "Person",
            person_id,
            "deleted."
        )


    # ========================================================
    # CLEAR PEOPLE
    # ========================================================

    def clear_people(self):

        self.people = []


        if os.path.exists(
            PEOPLE_FILE
        ):

            os.remove(
                PEOPLE_FILE
            )


        # ----------------------------------------------------
        # BLUETOOTH RESET
        # ----------------------------------------------------

        self.send_bluetooth(
            "RESET"
        )


        print(
            "All registered people deleted."
        )


    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        self.running = False


        # ----------------------------------------------------
        # CLOSE CAMERA
        # ----------------------------------------------------

        if self.camera is not None:

            try:

                self.camera.stop()

            except Exception:

                pass


            self.camera = None


        # ----------------------------------------------------
        # CLOSE BLUETOOTH
        # ----------------------------------------------------

        if self.bluetooth is not None:

            try:

                self.bluetooth.close()

            except Exception:

                pass


            self.bluetooth = None


        cv2.destroyAllWindows()
