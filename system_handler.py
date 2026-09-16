import cv2
import os
import shutil
import time

from camera_handler import CameraHandler
from prescription_handler import PrescriptionHandler
from rtc_handler import RTCHandler
from fingerprint_handler import FingerprintHandler


class SystemHandler:

    # =========================================================
    # INIT
    # =========================================================

    def __init__(self):

        # =====================================================
        # CAMERA
        # =====================================================

        self.camera = CameraHandler()

        # =====================================================
        # PRESCRIPTION
        # =====================================================

        self.prescription = PrescriptionHandler()

        # =====================================================
        # RTC
        # =====================================================

        self.rtc = RTCHandler(
            self.prescription
        )

        # =====================================================
        # FINGERPRINT
        # =====================================================

        self.fingerprint = FingerprintHandler(
            port="/dev/serial0",
            baudrate=57600
        )

        # =====================================================
        # STATE
        # =====================================================

        self.last_person_id = None

        self.fingerprint_busy = False

        self.last_command = None
        self.last_command_time = 0

        self.command_cooldown = 0.5

        # =====================================================
        # PENDING FACE REGISTRATION
        # =====================================================

        self.pending_enrollment = None

    # =========================================================
    # MENU
    # =========================================================

    def show_menu(self):

        print()
        print("================================")
        print("          LINGAP SYSTEM")
        print("================================")
        print("E = Register new face")
        print("R = Face recognition")
        print("P = Add prescription")
        print("L = List people")
        print("D = Delete one person")
        print()
        print("F = Register fingerprint")
        print("G = Fingerprint login")
        print("H = Reset fingerprints")
        print()
        print("X = FULL SYSTEM RESET")
        print("Q = Quit")
        print("================================")
        print()

    # =========================================================
    # CLEAR KEY BUFFER
    # =========================================================

    def clear_key_buffer(self):

        for _ in range(10):

            cv2.waitKey(1)

        time.sleep(0.1)

    # =========================================================
    # GET NEXT PERSON ID
    # =========================================================

    def get_next_person_id(self):

        people = self.camera.get_people()

        if not people:

            return 1

        used_ids = set()

        for person in people:

            try:

                used_ids.add(
                    int(person["id"])
                )

            except Exception:

                pass

        new_id = 1

        while new_id in used_ids:

            new_id += 1

        return new_id

    # =========================================================
    # FACE ENROLLMENT
    #
    # IMPORTANT FLOW:
    #
    # E
    # ↓
    # Are you a new user? Y/N
    # ↓
    # Y → ask name
    # N → select existing ID
    # ↓
    # camera enrollment
    # =========================================================

    def enroll_face(self):

        self.camera.set_mode(
            "idle"
        )

        self.pending_enrollment = None

        print()
        print("================================")
        print("       FACE REGISTRATION")
        print("================================")
        print()
        print("Y - Yes, I am a new user")
        print("N - No, I already have an account")
        print("0 - Cancel")
        print()

        while True:

            answer = input(
                "Are you a new user? Y/N: "
            ).strip().lower()

            # =================================================
            # CANCEL
            # =================================================

            if answer == "0":

                print()
                print(
                    "Face registration cancelled."
                )
                print()

                return

            # =================================================
            # NEW USER
            # =================================================

            if answer in (
                "y",
                "yes"
            ):

                print()
                print("================================")
                print("          NEW ACCOUNT")
                print("================================")
                print()

                # ---------------------------------------------
                # ASK NAME
                # ---------------------------------------------

                while True:

                    name = input(
                        "Enter your name: "
                    ).strip()

                    if not name:

                        print(
                            "Name cannot be empty."
                        )

                        continue

                    # -----------------------------------------
                    # DUPLICATE NAME
                    # -----------------------------------------

                    duplicate = False

                    for person in self.camera.get_people():

                        existing_name = str(
                            person.get(
                                "name",
                                ""
                            )
                        ).strip().lower()

                        if (
                            existing_name
                            ==
                            name.lower()
                        ):

                            duplicate = True

                            break

                    if duplicate:

                        print()
                        print(
                            "That name already exists."
                        )
                        print(
                            "Choose N if you already have an account."
                        )
                        print()

                        continue

                    break

                # ---------------------------------------------
                # ID
                # ---------------------------------------------

                person_id = (
                    self.get_next_person_id()
                )

                person_name = name

                print()
                print("================================")
                print("       REGISTRATION INFO")
                print("================================")
                print(
                    "Name:",
                    person_name
                )
                print(
                    "Person ID:",
                    person_id
                )
                print("================================")
                print()

                print(
                    "Look at the camera."
                )

                print(
                    "Face enrollment starting..."
                )

                print()

                # ---------------------------------------------
                # STORE INFO
                # ---------------------------------------------

                self.pending_enrollment = {

                    "person_id":
                        person_id,

                    "person_name":
                        person_name,

                    "new_user":
                        True
                }

                # ---------------------------------------------
                # START CAMERA
                # ---------------------------------------------

                self.camera.set_mode(
                    "enroll"
                )

                return

            # =================================================
            # EXISTING USER
            # =================================================

            elif answer in (
                "n",
                "no"
            ):

                people = (
                    self.camera.get_people()
                )

                if not people:

                    print()
                    print("================================")
                    print("       NO EXISTING USERS")
                    print("================================")
                    print(
                        "There are no registered accounts."
                    )
                    print(
                        "Choose Y to create a new account."
                    )
                    print()

                    continue

                print()
                print("================================")
                print("       EXISTING ACCOUNTS")
                print("================================")

                sorted_people = sorted(
                    people,
                    key=lambda person:
                        int(person["id"])
                )

                for person in sorted_people:

                    print(
                        "ID:",
                        person["id"],
                        "| NAME:",
                        person["name"]
                    )

                print()
                print("0 = Cancel")
                print("================================")
                print()

                # ---------------------------------------------
                # SELECT ID
                # ---------------------------------------------

                while True:

                    choice = input(
                        "Enter your Person ID: "
                    ).strip()

                    try:

                        selected_id = int(
                            choice
                        )

                    except ValueError:

                        print(
                            "Please enter a valid ID."
                        )

                        continue

                    if selected_id == 0:

                        print(
                            "Face registration cancelled."
                        )

                        return

                    person = (
                        self.camera.get_person(
                            selected_id
                        )
                    )

                    if person is None:

                        print(
                            "That ID does not exist."
                        )

                        continue

                    person_id = int(
                        person["id"]
                    )

                    person_name = str(
                        person["name"]
                    )

                    print()
                    print("================================")
                    print("       SELECTED ACCOUNT")
                    print("================================")
                    print(
                        "Name:",
                        person_name
                    )
                    print(
                        "Person ID:",
                        person_id
                    )
                    print("================================")
                    print()

                    confirm = input(
                        "Is this your account? Y/N: "
                    ).strip().lower()

                    if confirm in (
                        "y",
                        "yes"
                    ):

                        break

                    if confirm in (
                        "n",
                        "no"
                    ):

                        print(
                            "Choose another account."
                        )

                        continue

                    print(
                        "Please enter Y or N."
                    )

                # ---------------------------------------------
                # STORE INFO
                # ---------------------------------------------

                self.pending_enrollment = {

                    "person_id":
                        person_id,

                    "person_name":
                        person_name,

                    "new_user":
                        False
                }

                print()
                print(
                    "Look at the camera."
                )

                print(
                    "Face enrollment starting..."
                )

                print()

                # ---------------------------------------------
                # START CAMERA
                # ---------------------------------------------

                self.camera.set_mode(
                    "enroll"
                )

                return

            # =================================================
            # INVALID
            # =================================================

            else:

                print()
                print(
                    "Please enter Y, N, or 0."
                )
                print()

    # =========================================================
    # REGISTER FINGERPRINT
    # =========================================================

    def register_fingerprint(self):

        if self.fingerprint_busy:

            print()
            print(
                "Fingerprint operation already running."
            )
            print()

            return

        self.fingerprint_busy = True

        try:

            print()
            print("================================")
            print("     FINGERPRINT REGISTRATION")
            print("================================")
            print()

            if not self.fingerprint.is_connected():

                print(
                    "Fingerprint sensor is not connected."
                )

                return

            self.camera.set_mode(
                "idle"
            )

            print()
            print("Y - Yes, I already have an account")
            print("N - No, create a new account")
            print("0 - Cancel")
            print()

            while True:

                answer = input(
                    "Do you have an account? Y/N: "
                ).strip().lower()

                if answer in (
                    "y",
                    "yes"
                ):

                    people = (
                        self.camera.get_people()
                    )

                    if not people:

                        print()
                        print(
                            "There are no accounts stored."
                        )
                        print()

                        continue

                    print()
                    print("================================")
                    print("        EXISTING ACCOUNTS")
                    print("================================")

                    sorted_people = sorted(
                        people,
                        key=lambda person:
                            int(person["id"])
                    )

                    for person in sorted_people:

                        print(
                            "ID:",
                            person["id"],
                            "| NAME:",
                            person["name"]
                        )

                    print()
                    print("0 = Cancel")
                    print()

                    while True:

                        choice = input(
                            "Enter the ID to register fingerprint: "
                        ).strip()

                        try:

                            selected_id = int(
                                choice
                            )

                        except ValueError:

                            print(
                                "Please enter a valid ID."
                            )

                            continue

                        if selected_id == 0:

                            return

                        person = (
                            self.camera.get_person(
                                selected_id
                            )
                        )

                        if person is None:

                            print(
                                "That ID does not exist."
                            )

                            continue

                        person_id = int(
                            person["id"]
                        )

                        person_name = str(
                            person["name"]
                        )

                        confirm = input(
                            "Register fingerprint for "
                            + person_name
                            + "? Y/N: "
                        ).strip().lower()

                        if confirm in (
                            "y",
                            "yes"
                        ):

                            break

                    result = (
                        self.fingerprint.enroll(
                            person_id=person_id,
                            person_name=person_name,
                            replace=True
                        )
                    )

                    if result:

                        print()
                        print(
                            "FINGERPRINT REGISTERED."
                        )
                        print(
                            "ID:",
                            person_id
                        )
                        print(
                            "Name:",
                            person_name
                        )

                    return

                elif answer in (
                    "n",
                    "no"
                ):

                    print()
                    print("================================")
                    print("          NEW ACCOUNT")
                    print("================================")
                    print()

                    while True:

                        name = input(
                            "Enter your name: "
                        ).strip()

                        if not name:

                            print(
                                "Name cannot be empty."
                            )

                            continue

                        duplicate = False

                        for person in self.camera.get_people():

                            if str(
                                person.get(
                                    "name",
                                    ""
                                )
                            ).strip().lower() == name.lower():

                                duplicate = True

                                break

                        if duplicate:

                            print(
                                "That name already exists."
                            )

                            continue

                        break

                    person_id = (
                        self.get_next_person_id()
                    )

                    result = (
                        self.fingerprint.enroll(
                            person_id=person_id,
                            person_name=name,
                            replace=False
                        )
                    )

                    if not result:

                        print(
                            "Fingerprint registration failed."
                        )

                        return

                    self.camera.people.append(
                        {
                            "id":
                                person_id,

                            "name":
                                name,

                            "new_user":
                                True,

                            "encoding":
                                None
                        }
                    )

                    self.camera.save_people()

                    print()
                    print("================================")
                    print("       NEW ACCOUNT CREATED")
                    print("================================")
                    print(
                        "Name:",
                        name
                    )
                    print(
                        "Person ID:",
                        person_id
                    )
                    print(
                        "Fingerprint ID:",
                        person_id
                    )
                    print("================================")
                    print()

                    self.camera.send_bluetooth(
                        "FINGERPRINT_REGISTERED|"
                        + str(person_id)
                        + "|"
                        + name
                    )

                    return

                elif answer == "0":

                    print(
                        "Fingerprint registration cancelled."
                    )

                    return

                else:

                    print(
                        "Please enter Y, N, or 0."
                    )

        finally:

            self.fingerprint_busy = False

            self.camera.set_mode(
                "idle"
            )

            self.clear_key_buffer()

    # =========================================================
    # FINGERPRINT LOGIN
    # =========================================================

    def fingerprint_login(self):

        if self.fingerprint_busy:

            print(
                "Fingerprint login is already running."
            )

            return

        self.fingerprint_busy = True

        try:

            print()
            print("================================")
            print("       FINGERPRINT LOGIN")
            print("================================")
            print()

            if not self.fingerprint.is_connected():

                print(
                    "Fingerprint sensor is not connected."
                )

                return

            self.camera.set_mode(
                "idle"
            )

            result = (
                self.fingerprint.login(
                    timeout=30
                )
            )

            if result is None:

                print(
                    "Fingerprint login failed."
                )

                return

            person_id = int(
                result["id"]
            )

            person = (
                self.camera.get_person(
                    person_id
                )
            )

            if person is None:

                print()
                print(
                    "PERSON NOT FOUND"
                )
                print(
                    "Fingerprint ID:",
                    person_id
                )

                self.fingerprint.speak(
                    "Account not found."
                )

                self.fingerprint.send_bluetooth(
                    "LOGIN_FAILED"
                )

                return

            person_name = str(
                person["name"]
            )

            print()
            print("================================")
            print("         LOGIN SUCCESS")
            print("================================")
            print(
                "Name:",
                person_name
            )
            print(
                "Person ID:",
                person_id
            )
            print(
                "Fingerprint accuracy:",
                result["accuracy"]
            )
            print("================================")
            print()

            self.fingerprint.speak(
                person_name
                + ", login successful."
            )

            try:

                self.rtc.acknowledge(
                    person_id
                )

            except Exception as error:

                print(
                    "RTC acknowledge error:",
                    error
                )

            message = (
                "LOGIN|"
                + str(person_id)
                + "|"
                + person_name
            )

            self.fingerprint.send_bluetooth(
                message
            )

            data = (
                self.prescription.load(
                    person_id
                )
            )

            if data is None:

                print(
                    "NO PRESCRIPTION ASSIGNED."
                )

            else:

                self.prescription.display(
                    data
                )

        finally:

            self.fingerprint_busy = False

            self.camera.set_mode(
                "idle"
            )

            self.clear_key_buffer()

    # =========================================================
    # RESET FINGERPRINTS
    # =========================================================

    def reset_fingerprints(self):

        if not self.fingerprint.is_connected():

            print(
                "Fingerprint sensor is not connected."
            )

            return

        self.camera.set_mode(
            "idle"
        )

        self.fingerprint.reset_all()

        self.clear_key_buffer()

    # =========================================================
    # ASSIGN PRESCRIPTION
    # =========================================================

    def assign_prescription(self):

        people = self.camera.get_people()

        if not people:

            print(
                "No people registered."
            )

            return

        self.camera.set_mode(
            "idle"
        )

        print()

        for person in people:

            print(
                person["id"],
                "=",
                person["name"]
            )

        print()

        try:

            person_id = int(
                input(
                    "Enter Person ID: "
                ).strip()
            )

        except ValueError:

            print(
                "Invalid Person ID."
            )

            return

        person = (
            self.camera.get_person(
                person_id
            )
        )

        if person is None:

            print(
                "Person not found."
            )

            return

        print()
        print(
            "Selected:",
            person["name"]
        )
        print()

        confirm = input(
            "Continue? Y/N: "
        ).strip().lower()

        if confirm not in (
            "y",
            "yes"
        ):

            print(
                "Cancelled."
            )

            return

        data = (
            self.prescription.read_from_camera(
                self.camera,
                person_id,
                person["name"]
            )
        )

        if data is not None:

            self.rtc.clear_triggers_for_person(
                person_id
            )

            self.camera.send_bluetooth(
                "PRESCRIPTION_ASSIGNED|"
                + str(person_id)
                + "|"
                + str(person["name"])
            )

            print()
            print("================================")
            print("PRESCRIPTION ASSIGNED")
            print("================================")
            print(
                "ID:",
                person_id
            )
            print(
                "NAME:",
                person["name"]
            )
            print("================================")
            print()

        else:

            print(
                "Prescription assignment failed."
            )

        self.camera.set_mode(
            "idle"
        )

    # =========================================================
    # LIST PEOPLE
    # =========================================================

    def list_people(self):

        people = (
            self.camera.get_people()
        )

        print()
        print("================================")
        print("       REGISTERED PEOPLE")
        print("================================")

        if not people:

            print(
                "No people registered."
            )

        else:

            for person in people:

                person_id = int(
                    person["id"]
                )

                print()
                print(
                    "ID:",
                    person_id
                )

                print(
                    "Name:",
                    person["name"]
                )

                data = (
                    self.prescription.load(
                        person_id
                    )
                )

                print(
                    "Prescription:",
                    "YES" if data else "NO"
                )

                if self.fingerprint.is_connected():

                    try:

                        exists = (
                            self.fingerprint
                            .template_exists(
                                person_id
                            )
                        )

                        print(
                            "Fingerprint:",
                            "YES" if exists else "NO"
                        )

                    except Exception:

                        pass

        print()
        print("================================")

    # =========================================================
    # DELETE PERSON
    # =========================================================

    def delete_person(self):

        people = (
            self.camera.get_people()
        )

        if not people:

            print(
                "No people registered."
            )

            return

        self.camera.set_mode(
            "idle"
        )

        print()

        for person in people:

            print(
                person["id"],
                "=",
                person["name"]
            )

        print()

        try:

            person_id = int(
                input(
                    "Enter Person ID to delete: "
                ).strip()
            )

        except ValueError:

            print(
                "Invalid Person ID."
            )

            return

        person = (
            self.camera.get_person(
                person_id
            )
        )

        if person is None:

            print(
                "Person not found."
            )

            return

        confirm = input(
            "Type DELETE to confirm: "
        ).strip()

        if confirm != "DELETE":

            print(
                "Cancelled."
            )

            return

        self.camera.delete_person(
            person_id
        )

        self.prescription.delete(
            person_id
        )

        self.rtc.clear_triggers_for_person(
            person_id
        )

        if self.fingerprint.is_connected():

            try:

                self.fingerprint.delete(
                    person_id
                )

            except Exception as error:

                print(
                    "Fingerprint deletion error:",
                    error
                )

        print()
        print(
            "Person",
            person_id,
            "fully deleted."
        )
        print()

    # =========================================================
    # FULL SYSTEM RESET
    # =========================================================

    def reset_all_data(self):

        self.camera.set_mode(
            "idle"
        )

        confirm = input(
            "Type RESET EVERYTHING to confirm: "
        ).strip()

        if confirm != "RESET EVERYTHING":

            print(
                "Cancelled."
            )

            return

        self.camera.clear_people()

        if os.path.exists(
            "prescriptions"
        ):

            shutil.rmtree(
                "prescriptions"
            )

        os.makedirs(
            "prescriptions",
            exist_ok=True
        )

        self.rtc.triggered = {}

        self.rtc.stop_buzzer()

        self.rtc.active_person_id = None

        if self.fingerprint.is_connected():

            self.fingerprint.reset_all()

        self.pending_enrollment = None

        print()
        print("================================")
        print("      SYSTEM RESET COMPLETE")
        print("================================")
        print(
            "All people deleted."
        )
        print(
            "All prescriptions deleted."
        )
        print(
            "All fingerprints deleted."
        )
        print("================================")
        print()

    # =========================================================
    # HANDLE KEY
    # =========================================================

    def handle_key(
        self,
        key
    ):

        key = key.lower()

        now = time.time()

        if (
            key == self.last_command
            and
            now - self.last_command_time
            <
            self.command_cooldown
        ):

            return True

        self.last_command = key
        self.last_command_time = now

        if key == "e":

            self.enroll_face()

        elif key == "r":

            self.recognize_face()

        elif key == "p":

            self.assign_prescription()

        elif key == "l":

            self.list_people()

        elif key == "d":

            self.delete_person()

        elif key == "f":

            self.register_fingerprint()

        elif key == "g":

            self.fingerprint_login()

        elif key == "h":

            self.reset_fingerprints()

        elif key == "x":

            self.reset_all_data()

        elif key == "q":

            return False

        return True

    # =========================================================
    # RECOGNIZE FACE
    # =========================================================

    def recognize_face(self):

        print()
        print(
            "Face recognition mode."
        )

        self.last_person_id = None

        self.camera.set_mode(
            "recognize"
        )

    # =========================================================
    # PROCESS FRAME
    # =========================================================

    def process_frame(
        self,
        frame
    ):

        # -----------------------------------------------------
        # RTC
        # -----------------------------------------------------

        self.rtc.check_all_people(
            self.camera.get_people()
        )

        # -----------------------------------------------------
        # FACE ENROLLMENT
        # -----------------------------------------------------

        if self.camera.mode == "enroll":

            if self.pending_enrollment is None:

                self.camera.set_mode(
                    "idle"
                )

                return frame

            person_id = int(
                self.pending_enrollment[
                    "person_id"
                ]
            )

            person_name = str(
                self.pending_enrollment[
                    "person_name"
                ]
            )

            new_user = bool(
                self.pending_enrollment[
                    "new_user"
                ]
            )

            frame, success, status = (
                self.camera.enroll(
                    frame,
                    person_id=person_id,
                    person_name=person_name,
                    new_user=new_user
                )
            )

            if success:

                self.pending_enrollment = None

                self.camera.set_mode(
                    "idle"
                )

                print()
                print(
                    "Face enrollment complete."
                )
                print()

        # -----------------------------------------------------
        # FACE RECOGNITION
        # -----------------------------------------------------

        elif self.camera.mode == "recognize":

            frame, person = (
                self.camera.recognize(
                    frame
                )
            )

            if person is not None:

                person_id = int(
                    person["id"]
                )

                if person_id != self.last_person_id:

                    self.last_person_id = (
                        person_id
                    )

                    try:

                        self.rtc.acknowledge(
                            person_id
                        )

                    except Exception as error:

                        print(
                            "RTC error:",
                            error
                        )

                    # -----------------------------------------
                    # BLUETOOTH
                    # -----------------------------------------

                    message = (
                        "LOGIN|"
                        + str(person_id)
                        + "|"
                        + str(person["name"])
                    )

                    self.camera.send_bluetooth(
                        message
                    )

                    # -----------------------------------------
                    # SHOW PERSON
                    # -----------------------------------------

                    self.show_recognized_person(
                        person
                    )

                    # -----------------------------------------
                    # STOP RECOGNITION
                    # -----------------------------------------

                    self.camera.set_mode(
                        "idle"
                    )

            else:

                self.last_person_id = None

        return frame

    # =========================================================
    # SHOW RECOGNIZED PERSON
    # =========================================================

    def show_recognized_person(
        self,
        person
    ):

        person_id = int(
            person["id"]
        )

        print()
        print("================================")
        print("       PERSON RECOGNIZED")
        print("================================")
        print(
            "ID:",
            person_id
        )
        print(
            "Name:",
            person["name"]
        )

        data = (
            self.prescription.load(
                person_id
            )
        )

        if data is not None:

            self.prescription.display(
                data
            )

        else:

            print(
                "NO PRESCRIPTION ASSIGNED"
            )

        print(
            "================================"
        )

    # =========================================================
    # MAIN LOOP
    # =========================================================

    def run(self):

        self.camera.start()

        self.show_menu()

        try:

            while self.camera.running:

                frame = (
                    self.camera.capture()
                )

                if frame is None:

                    continue

                frame = (
                    self.process_frame(
                        frame
                    )
                )

                cv2.imshow(
                    "Face System",
                    frame
                )

                key = (
                    cv2.waitKey(1)
                    &
                    0xFF
                )

                if key == 255:

                    continue

                if key == ord("q"):

                    break

                valid_keys = (
                    ord("e"),
                    ord("r"),
                    ord("p"),
                    ord("l"),
                    ord("d"),
                    ord("f"),
                    ord("g"),
                    ord("h"),
                    ord("x")
                )

                if key in valid_keys:

                    command = chr(
                        key
                    )

                    if not self.handle_key(
                        command
                    ):

                        break

                    self.clear_key_buffer()

        finally:

            self.shutdown()

    # =========================================================
    # SHUTDOWN
    # =========================================================

    def shutdown(self):

        print()
        print(
            "Shutting down..."
        )

        try:

            self.camera.stop()

        except Exception as error:

            print(
                "Camera shutdown error:",
                error
            )

        try:

            self.fingerprint.close()

        except Exception as error:

            print(
                "Fingerprint shutdown error:",
                error
            )

        try:

            self.rtc.cleanup()

        except Exception as error:

            print(
                "RTC cleanup error:",
                error
            )

        cv2.destroyAllWindows()

        print()
        print(
            "System stopped."
        )


