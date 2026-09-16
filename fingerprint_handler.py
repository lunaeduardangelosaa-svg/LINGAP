import time
import subprocess
import serial

from pyfingerprint.pyfingerprint import (
    PyFingerprint,
    FINGERPRINT_CHARBUFFER1,
    FINGERPRINT_CHARBUFFER2
)


# ============================================================
# FINGERPRINT
# ============================================================

FINGERPRINT_PORT = "/dev/serial0"
FINGERPRINT_BAUD = 57600

FINGERPRINT_ADDRESS = 0xFFFFFFFF
FINGERPRINT_PASSWORD = 0x00000000


# ============================================================
# BLUETOOTH
# ============================================================

BLUETOOTH_PORT = "/dev/ttyAMA2"
BLUETOOTH_BAUD = 9600


class FingerprintHandler:

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        port=FINGERPRINT_PORT,
        baudrate=FINGERPRINT_BAUD,
        address=FINGERPRINT_ADDRESS,
        password=FINGERPRINT_PASSWORD
    ):

        self.port = port
        self.baudrate = baudrate
        self.address = address
        self.password = password

        self.sensor = None
        self.connected = False

        self.connect()

    # ========================================================
    # SPEAK
    # ========================================================

    def speak(self, text):

        try:

            subprocess.Popen(
                [
                    "espeak",
                    "-v", "en-us+f3",
                    "-s", "150",
                    str(text)
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        except Exception as error:

            print(
                "eSpeak error:",
                error
            )

    # ========================================================
    # BLUETOOTH
    # ========================================================

    def send_bluetooth(self, message):

        bluetooth = None

        try:

            message = str(message).strip()

            data = (
                message + "\n"
            ).encode(
                "ascii",
                errors="replace"
            )

            print()
            print("================================")
            print("       BLUETOOTH SEND")
            print("================================")
            print("PORT:", BLUETOOTH_PORT)
            print("BAUD:", BLUETOOTH_BAUD)
            print("SENT:", message)
            print("BYTES:", repr(data))
            print("================================")

            bluetooth = serial.Serial(
                port=BLUETOOTH_PORT,
                baudrate=BLUETOOTH_BAUD,
                timeout=1,
                write_timeout=2
            )

            time.sleep(0.3)

            bluetooth.reset_input_buffer()
            bluetooth.reset_output_buffer()

            bluetooth.write(data)
            bluetooth.flush()

            print(
                "Bluetooth message sent successfully."
            )

            return True

        except Exception as error:

            print()
            print("================================")
            print("      BLUETOOTH ERROR")
            print("================================")
            print("Error type:", type(error).__name__)
            print("Error:", error)
            print("================================")
            print()

            return False

        finally:

            if bluetooth is not None:

                try:
                    bluetooth.close()

                except Exception:
                    pass

    # ========================================================
    # CONNECT
    # ========================================================

    def connect(self):

        print()
        print("================================")
        print("     FINGERPRINT SENSOR")
        print("================================")
        print("Port:", self.port)
        print("Baudrate:", self.baudrate)

        try:

            self.sensor = PyFingerprint(
                self.port,
                self.baudrate,
                self.address,
                self.password
            )

            print(
                "Verifying sensor..."
            )

            if not self.sensor.verifyPassword():

                raise RuntimeError(
                    "Incorrect fingerprint sensor password."
                )

            self.connected = True

            print()
            print(
                "Fingerprint sensor connected."
            )

            print(
                "Sensor capacity:",
                self.sensor.getStorageCapacity()
            )

            print(
                "Stored fingerprints:",
                self.sensor.getTemplateCount()
            )

            print("================================")
            print()

            return True

        except Exception as error:

            self.connected = False
            self.sensor = None

            print()
            print("================================")
            print(" FINGERPRINT CONNECTION FAILED")
            print("================================")
            print("Error:", error)
            print()
            print("AS608 wiring:")
            print("VCC -> Pin 2 (5V)")
            print("GND -> Pin 6 (GND)")
            print("TX  -> Pin 10 (GPIO15 / RXD)")
            print("RX  -> Pin 8  (GPIO14 / TXD)")
            print("================================")
            print()

            return False

    # ========================================================
    # CONNECTION STATUS
    # ========================================================

    def is_connected(self):

        return self.connected

    # ========================================================
    # CAPACITY
    # ========================================================

    def get_capacity(self):

        if not self.connected:
            return 0

        try:

            return self.sensor.getStorageCapacity()

        except Exception:

            return 0

    # ========================================================
    # COUNT
    # ========================================================

    def get_count(self):

        if not self.connected:
            return 0

        try:

            return self.sensor.getTemplateCount()

        except Exception:

            return 0

    # ========================================================
    # VALID ID
    # ========================================================

    def valid_id(self, person_id):

        if not self.connected:
            return False

        try:

            person_id = int(person_id)

        except Exception:

            return False

        capacity = self.get_capacity()

        return (
            0 <= person_id < capacity
        )

    # ========================================================
    # CHECK IF TEMPLATE EXISTS
    # ========================================================

    def template_exists(self, template_id):

        if not self.connected:
            return False

        if not self.valid_id(template_id):
            return False

        try:

            return self.sensor.loadTemplate(
                int(template_id),
                FINGERPRINT_CHARBUFFER1
            )

        except Exception:

            return False

    # ========================================================
    # WAIT FOR FINGER REMOVED
    # ========================================================

    def wait_for_finger_removed(
        self,
        timeout=5
    ):

        if not self.connected:
            return False

        start = time.time()

        while (
            time.time() - start
            < timeout
        ):

            try:

                if not self.sensor.readImage():

                    return True

            except Exception:

                return True

            time.sleep(0.1)

        return False

    # ========================================================
    # WAIT FOR VALID FINGER
    # ========================================================

    def wait_for_valid_finger(
        self,
        buffer_id,
        timeout=30
    ):

        if not self.connected:
            return False

        print()
        print(
            "WAITING FOR FINGER..."
        )

        start = time.time()

        while (
            time.time() - start
            < timeout
        ):

            try:

                image = self.sensor.readImage()

                if image is not True:

                    time.sleep(0.1)
                    continue

                print()
                print(
                    "Fingerprint detected."
                )

                print(
                    "Reading fingerprint..."
                )

                try:

                    converted = (
                        self.sensor.convertImage(
                            buffer_id
                        )
                    )

                    if converted:

                        print()
                        print(
                            "GOOD SCAN."
                        )

                        return True

                    print()
                    print(
                        "Poor fingerprint scan."
                    )

                    print(
                        "Try again."
                    )

                except Exception as error:

                    print(
                        "Fingerprint conversion error:",
                        error
                    )

                time.sleep(0.5)

            except Exception:

                time.sleep(0.1)

        print()
        print("================================")
        print("      FINGERPRINT TIMEOUT")
        print("================================")
        print()

        return False

    # ========================================================
    # ENROLL FINGERPRINT
    #
    # IMPORTANT:
    # This function DOES NOT ask for the user.
    #
    # SystemHandler already knows:
    #
    #     person_id
    #     person_name
    #
    # ========================================================

    def enroll(
        self,
        person_id,
        person_name,
        replace=True
    ):

        if not self.connected:

            print(
                "Fingerprint sensor is not connected."
            )

            return False

        try:

            person_id = int(person_id)
            person_name = str(person_name)

        except Exception:

            print(
                "Invalid person information."
            )

            return False

        if not self.valid_id(person_id):

            print(
                "Invalid fingerprint ID:",
                person_id
            )

            return False

        print()
        print("================================")
        print("     REGISTER FINGERPRINT")
        print("================================")
        print("Name:", person_name)
        print("Person ID:", person_id)
        print("Fingerprint ID:", person_id)
        print("================================")
        print()

        # ====================================================
        # EXISTING TEMPLATE
        # ====================================================

        if self.template_exists(person_id):

            print()
            print(
                "A fingerprint already exists for:"
            )

            print(
                "Name:",
                person_name
            )

            print(
                "ID:",
                person_id
            )

            print()

            if not replace:

                print(
                    "Replacement disabled."
                )

                return False

            confirmation = input(
                "Replace existing fingerprint? Y/N: "
            ).strip().lower()

            if confirmation != "y":

                print(
                    "Fingerprint enrollment cancelled."
                )

                return False

            try:

                self.sensor.deleteTemplate(
                    person_id
                )

                print(
                    "Old fingerprint deleted."
                )

            except Exception as error:

                print(
                    "Could not delete old fingerprint:"
                )

                print(error)

                return False

        # ====================================================
        # SCAN 1
        # ====================================================

        print()
        print("================================")
        print("             SCAN 1")
        print("================================")
        print()

        print(
            "Place your finger on the sensor."
        )

        self.speak(
            "Place your finger on the sensor."
        )

        success = (
            self.wait_for_valid_finger(
                FINGERPRINT_CHARBUFFER1,
                30
            )
        )

        if not success:

            print(
                "First scan timed out."
            )

            return False

        print()
        print(
            "First scan accepted."
        )

        # ====================================================
        # CHECK DUPLICATE
        # ====================================================

        try:

            print()
            print(
                "Checking if fingerprint already exists..."
            )

            position, accuracy = (
                self.sensor.searchTemplate()
            )

            if position >= 0:

                # If it is the SAME ID we are replacing,
                # allow it because it was deleted above.
                if int(position) != person_id:

                    print()
                    print("================================")
                    print(" FINGERPRINT ALREADY REGISTERED")
                    print("================================")
                    print(
                        "Existing fingerprint ID:",
                        position
                    )
                    print(
                        "Accuracy:",
                        accuracy
                    )
                    print("================================")
                    print()

                    self.speak(
                        "This fingerprint is already registered."
                    )

                    self.wait_for_finger_removed()

                    return False

        except Exception:

            pass

        # ====================================================
        # REMOVE FINGER
        # ====================================================

        print()
        print(
            "Remove your finger."
        )

        self.speak(
            "Remove your finger."
        )

        self.wait_for_finger_removed()

        time.sleep(0.5)

        # ====================================================
        # SCAN 2
        # ====================================================

        print()
        print("================================")
        print("             SCAN 2")
        print("================================")
        print()

        print(
            "Place the same finger again."
        )

        self.speak(
            "Place the same finger again."
        )

        success = (
            self.wait_for_valid_finger(
                FINGERPRINT_CHARBUFFER2,
                30
            )
        )

        if not success:

            print(
                "Second scan timed out."
            )

            return False

        print()
        print(
            "Second scan accepted."
        )

        # ====================================================
        # COMPARE
        # ====================================================

        try:

            print()
            print(
                "Comparing both scans..."
            )

            accuracy = (
                self.sensor.compareCharacteristics()
            )

            print(
                "Comparison accuracy:",
                accuracy
            )

            if accuracy <= 0:

                print()
                print("================================")
                print("       SCANS DO NOT MATCH")
                print("================================")
                print()

                self.speak(
                    "The fingerprints do not match."
                )

                self.wait_for_finger_removed()

                return False

            print()
            print(
                "Scans match."
            )

            # =================================================
            # CREATE TEMPLATE
            # =================================================

            print()
            print(
                "Creating fingerprint template..."
            )

            created = (
                self.sensor.createTemplate()
            )

            if not created:

                print(
                    "Could not create fingerprint template."
                )

                return False

            print(
                "Fingerprint template created."
            )

            # =================================================
            # STORE TEMPLATE
            # =================================================

            print()
            print(
                "Saving fingerprint..."
            )

            print(
                "Fingerprint ID:",
                person_id
            )

            stored_id = (
                self.sensor.storeTemplate(
                    person_id
                )
            )

            print(
                "Stored fingerprint ID:",
                stored_id
            )

            self.wait_for_finger_removed()

            # =================================================
            # VERIFY ID
            # =================================================

            if int(stored_id) != person_id:

                print()
                print("================================")
                print("        ID MISMATCH")
                print("================================")
                print(
                    "Expected:",
                    person_id
                )
                print(
                    "Stored:",
                    stored_id
                )
                print("================================")
                print()

                return False

            # =================================================
            # SUCCESS
            # =================================================

            print()
            print("================================")
            print(" FINGERPRINT REGISTERED")
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
                "Fingerprint ID:",
                stored_id
            )
            print("================================")
            print()

            self.speak(
                "Fingerprint for "
                + person_name
                + " has been registered successfully."
            )

            # -------------------------------------------------
            # SEND TO APP
            # -------------------------------------------------

            message = (
                "FINGERPRINTREGISTER|"
                + str(person_id)
                + "|"
                + person_name
            )

            self.send_bluetooth(
                message
            )

            return {
                "id": person_id,
                "name": person_name,
                "success": True
            }

        except Exception as error:

            print()
            print("================================")
            print(" FINGERPRINT ENROLLMENT ERROR")
            print("================================")
            print(error)
            print("================================")
            print()

            return False

    # ========================================================
    # LOGIN
    # ========================================================

    def login(
        self,
        timeout=30,
        max_attempts=3
    ):

        if not self.connected:

            print(
                "Fingerprint sensor is not connected."
            )

            return None

        attempt = 0

        while attempt < max_attempts:

            attempt += 1

            print()
            print("================================")
            print("       FINGERPRINT LOGIN")
            print("================================")
            print(
                "Attempt:",
                attempt,
                "/",
                max_attempts
            )
            print("================================")
            print()

            print(
                "Place your finger on the sensor."
            )

            self.speak(
                "Place your finger on the sensor."
            )

            success = (
                self.wait_for_valid_finger(
                    FINGERPRINT_CHARBUFFER1,
                    timeout
                )
            )

            if not success:

                if attempt < max_attempts:

                    print(
                        "Try again."
                    )

                    continue

                self.speak(
                    "Fingerprint login failed."
                )

                self.send_bluetooth(
                    "LOGIN_FAILED"
                )

                return None

            try:

                position, accuracy = (
                    self.sensor.searchTemplate()
                )

                print()
                print(
                    "Fingerprint ID:",
                    position
                )

                print(
                    "Accuracy:",
                    accuracy
                )

                # ------------------------------------------------
                # REMOVE FINGER
                # ------------------------------------------------

                print()
                print(
                    "Remove your finger."
                )

                self.wait_for_finger_removed()

                # ------------------------------------------------
                # NOT FOUND
                # ------------------------------------------------

                if position < 0:

                    print()
                    print(
                        "Fingerprint not recognized."
                    )

                    if attempt < max_attempts:

                        self.speak(
                            "Fingerprint not recognized. Please try again."
                        )

                        continue

                    self.speak(
                        "Fingerprint login failed."
                    )

                    self.send_bluetooth(
                        "LOGIN_FAILED"
                    )

                    return None

                # ------------------------------------------------
                # SUCCESS
                # ------------------------------------------------

                print()
                print("================================")
                print(" FINGERPRINT MATCHED")
                print("================================")
                print(
                    "Fingerprint ID:",
                    position
                )
                print(
                    "Accuracy:",
                    accuracy
                )
                print("================================")
                print()

                return {
                    "id": int(position),
                    "accuracy": accuracy
                }

            except Exception as error:

                print()
                print("================================")
                print("   FINGERPRINT LOGIN ERROR")
                print("================================")
                print(error)
                print("================================")

                if attempt < max_attempts:

                    time.sleep(0.5)

                    continue

                self.send_bluetooth(
                    "LOGIN_FAILED"
                )

                return None

        return None

    # ========================================================
    # DELETE
    # ========================================================

    def delete(self, person_id):

        if not self.connected:
            return False

        if not self.valid_id(person_id):
            return False

        try:

            if not self.template_exists(person_id):

                print(
                    "No fingerprint found for ID:",
                    person_id
                )

                return False

            self.sensor.deleteTemplate(
                int(person_id)
            )

            print(
                "Fingerprint deleted:",
                person_id
            )

            self.send_bluetooth(
                "DELETE|"
                + str(person_id)
            )

            return True

        except Exception as error:

            print(
                "Fingerprint deletion failed:",
                error
            )

            return False

    # ========================================================
    # CLEAR DATABASE
    # ========================================================

    def clear_database(self):

        if not self.connected:

            raise RuntimeError(
                "Fingerprint sensor is not connected."
            )

        self.sensor.clearDatabase()

        return True

    # ========================================================
    # RESET ALL
    # ========================================================

    def reset_all(self):

        if not self.connected:

            print(
                "Fingerprint sensor is not connected."
            )

            return False

        print()
        print("================================")
        print("   RESET FINGERPRINT DATABASE")
        print("================================")
        print()

        confirmation = input(
            "Type RESET FINGERPRINT to continue: "
        ).strip()

        if confirmation != "RESET FINGERPRINT":

            print(
                "Fingerprint reset cancelled."
            )

            return False

        try:

            self.clear_database()

            print()
            print("================================")
            print(" FINGERPRINT RESET COMPLETE")
            print("================================")
            print()

            self.speak(
                "All fingerprints have been deleted."
            )

            self.send_bluetooth(
                "RESET"
            )

            return True

        except Exception as error:

            print(
                "Could not reset fingerprint database:"
            )

            print(error)

            return False

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.sensor = None
        self.connected = False

        print(
            "Fingerprint sensor closed."
        )
