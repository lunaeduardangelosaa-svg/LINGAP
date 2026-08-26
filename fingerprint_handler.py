import time
import subprocess
import serial

from pyfingerprint.pyfingerprint import (
    PyFingerprint,
    FINGERPRINT_CHARBUFFER1,
    FINGERPRINT_CHARBUFFER2
)


# =========================================================
# AS608 FINGERPRINT UART
# =========================================================

FINGERPRINT_PORT = "/dev/serial0"
FINGERPRINT_BAUD = 57600


# =========================================================
# HC-05 BLUETOOTH UART
# =========================================================

BLUETOOTH_PORT = "/dev/ttyAMA2"
BLUETOOTH_BAUD = 9600


class FingerprintHandler:

    # =====================================================
    # INITIALIZE
    # =====================================================

    def __init__(
        self,
        port=FINGERPRINT_PORT,
        baudrate=FINGERPRINT_BAUD,
        address=0xFFFFFFFF,
        password=0x00000000
    ):

        self.port = port
        self.baudrate = baudrate

        self.address = address
        self.password = password

        self.sensor = None
        self.connected = False

        self.connect()


    # =====================================================
    # TEXT TO SPEECH
    # =====================================================

    def speak(self, text):

        try:

            subprocess.Popen(
                [
                    "espeak",
                    "-s", "150",
                    "-a", "150",
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


    # =====================================================
    # BLUETOOTH SEND
    # =====================================================

    def send_bluetooth(
        self,
        message
    ):

        bluetooth = None

        try:

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
            print("================================")
            print("       BLUETOOTH SEND")
            print("================================")

            print(
                "PORT:",
                BLUETOOTH_PORT
            )

            print(
                "BAUD:",
                BLUETOOTH_BAUD
            )

            print(
                "SENT:",
                message
            )

            print(
                "BYTES:",
                repr(data)
            )

            print("================================")


            # ------------------------------------------------
            # OPEN HC-05
            # ------------------------------------------------

            bluetooth = serial.Serial(

                port=BLUETOOTH_PORT,

                baudrate=BLUETOOTH_BAUD,

                timeout=1,

                write_timeout=2
            )


            # ------------------------------------------------
            # HC-05 STABILIZATION
            # ------------------------------------------------

            time.sleep(
                0.3
            )


            # ------------------------------------------------
            # CLEAR BUFFERS
            # ------------------------------------------------

            bluetooth.reset_input_buffer()

            bluetooth.reset_output_buffer()


            # ------------------------------------------------
            # SEND
            # ------------------------------------------------

            bluetooth.write(
                data
            )

            bluetooth.flush()


            # ------------------------------------------------
            # CONFIRM
            # ------------------------------------------------

            print(
                "SENT:",
                message
            )

            print("================================")
            print()

            return True


        except Exception as error:

            print()
            print("================================")
            print("      BLUETOOTH ERROR")
            print("================================")

            print(
                "Error type:",
                type(error).__name__
            )

            print(
                "Error:",
                error
            )

            print(
                "Port:",
                BLUETOOTH_PORT
            )

            print(
                "Baud:",
                BLUETOOTH_BAUD
            )

            print("================================")
            print()

            return False


        finally:

            if bluetooth is not None:

                try:

                    bluetooth.close()

                except Exception:

                    pass


    # =====================================================
    # CONNECT AS608
    # =====================================================

    def connect(self):

        print()
        print("================================")
        print("     FINGERPRINT SENSOR")
        print("================================")

        print(
            "Port:",
            self.port
        )

        print(
            "Baudrate:",
            self.baudrate
        )

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


            print()
            print(
                "HC-05 Bluetooth:"
            )

            print(
                "Port:",
                BLUETOOTH_PORT
            )

            print(
                "Baudrate:",
                BLUETOOTH_BAUD
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

            print(
                "Error:",
                error
            )

            print()

            print(
                "AS608 wiring:"
            )

            print(
                "VCC -> Pin 2 (5V)"
            )

            print(
                "GND -> Pin 6 (GND)"
            )

            print(
                "TX  -> Pin 10 (GPIO15 / RXD)"
            )

            print(
                "RX  -> Pin 8 (GPIO14 / TXD)"
            )

            print("================================")
            print()

            return False


    # =====================================================
    # STATUS
    # =====================================================

    def is_connected(self):

        return self.connected


    # =====================================================
    # CAPACITY
    # =====================================================

    def get_capacity(self):

        if not self.connected:

            return 0

        try:

            return (
                self.sensor
                .getStorageCapacity()
            )

        except Exception:

            return 0


    # =====================================================
    # COUNT
    # =====================================================

    def get_count(self):

        if not self.connected:

            return 0

        try:

            return (
                self.sensor
                .getTemplateCount()
            )

        except Exception:

            return 0


    # =====================================================
    # VALID ID
    # =====================================================

    def valid_id(
        self,
        person_id
    ):

        if not self.connected:

            return False

        capacity = self.get_capacity()

        return (

            isinstance(
                person_id,
                int
            )

            and

            person_id >= 0

            and

            person_id < capacity
        )


    # =====================================================
    # WAIT FOR FINGER REMOVED
    # =====================================================

    def wait_for_finger_removed(
        self,
        timeout=5,
        speak=True
    ):

        if not self.connected:

            return False


        if speak:

            self.speak(
                "Remove your finger."
            )


        start = time.time()


        while (
            time.time()
            -
            start
            <
            timeout
        ):

            try:

                if not self.sensor.readImage():

                    return True


            except Exception:

                return True


            time.sleep(
                0.1
            )


        return False


    # =====================================================
    # WAIT FOR VALID FINGER
    # =====================================================

    def wait_for_valid_finger(
        self,
        buffer_id,
        timeout=30,
        voice_message="Place your finger."
    ):

        if not self.connected:

            return False


        print()
        print(
            "WAITING FOR FINGER..."
        )

        print(
            voice_message
        )


        self.speak(
            voice_message
        )


        start = time.time()


        while (

            time.time()
            -
            start
            <
            timeout

        ):

            try:

                image = (
                    self.sensor
                    .readImage()
                )


                if image is not True:

                    time.sleep(
                        0.1
                    )

                    continue


                print()
                print(
                    "Fingerprint detected."
                )

                print(
                    "Checking fingerprint..."
                )


                self.speak(
                    "Fingerprint detected."
                )


                try:

                    converted = (
                        self.sensor
                        .convertImage(
                            buffer_id
                        )
                    )


                    if converted:

                        print()
                        print(
                            "GOOD SCAN."
                        )


                        self.speak(
                            "Good scan."
                        )


                        return True


                    print()
                    print(
                        "Poor fingerprint scan."
                    )

                    print(
                        "Try again."
                    )


                    self.speak(
                        "Poor scan. Please try again."
                    )


                except Exception:

                    print()
                    print(
                        "Poor fingerprint scan."
                    )


                    self.speak(
                        "Poor scan. Please try again."
                    )


                time.sleep(
                    0.5
                )


            except Exception:

                time.sleep(
                    0.1
                )


        print()
        print("================================")
        print("      FINGERPRINT TIMEOUT")
        print("================================")
        print()


        self.speak(
            "Fingerprint timed out."
        )


        return False


    # =====================================================
    # TEMPLATE EXISTS
    # =====================================================

    def template_exists(
        self,
        template_id
    ):

        if not self.connected:

            return False


        if not self.valid_id(
            template_id
        ):

            return False


        try:

            return (
                self.sensor
                .loadTemplate(
                    template_id,
                    FINGERPRINT_CHARBUFFER1
                )
            )


        except Exception:

            return False


    # =====================================================
    # ENROLL
    # =====================================================

    def enroll(
        self,
        person_id,
        replace=True,
        person_name=None
    ):

        if not self.connected:

            print(
                "Fingerprint sensor is not connected."
            )

            self.speak(
                "Fingerprint sensor is not connected."
            )

            return False


        if not self.valid_id(
            person_id
        ):

            print(
                "Invalid fingerprint ID:",
                person_id
            )

            self.speak(
                "Invalid fingerprint ID."
            )

            return False


        print()
        print("================================")
        print("     REGISTER FINGERPRINT")
        print("================================")

        print(
            "Person ID:",
            person_id
        )


        if person_name:

            print(
                "Person Name:",
                person_name
            )


        print()


        self.speak(
            "Registering fingerprint."
        )


        # =====================================================
        # EXISTING FINGERPRINT
        # =====================================================

        if self.template_exists(
            person_id
        ):

            print(
                "Fingerprint already exists for ID:",
                person_id
            )


            self.speak(
                "A fingerprint already exists for this person."
            )


            if not replace:

                print(
                    "Fingerprint registration cancelled."
                )

                return False


            confirmation = input(
                "Replace existing fingerprint? Y/N: "
            ).strip().lower()


            if confirmation != "y":

                print(
                    "Fingerprint registration cancelled."
                )

                self.speak(
                    "Fingerprint registration cancelled."
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

                print(
                    error
                )

                return False


        # =====================================================
        # SCAN 1
        # =====================================================

        print()
        print("================================")
        print("             SCAN 1")
        print("================================")
        print()


        success = (
            self.wait_for_valid_finger(

                FINGERPRINT_CHARBUFFER1,

                30,

                "Registering fingerprint. Place your finger."
            )
        )


        if not success:

            print(
                "First scan timed out."
            )

            self.speak(
                "First scan failed."
            )

            return False


        print()
        print(
            "First scan accepted."
        )


        self.speak(
            "First scan accepted."
        )


        # =====================================================
        # DUPLICATE CHECK
        # =====================================================

        try:

            print()
            print(
                "Checking if fingerprint already exists..."
            )


            position, accuracy = (
                self.sensor.searchTemplate()
            )


            if position >= 0:

                print()
                print("================================")
                print(" FINGERPRINT ALREADY REGISTERED")
                print("================================")

                print(
                    "Existing ID:",
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


        # =====================================================
        # REMOVE FINGER
        # =====================================================

        print()
        print(
            "Remove your finger."
        )


        self.wait_for_finger_removed(
            speak=True
        )


        time.sleep(
            0.5
        )


        # =====================================================
        # SCAN 2
        # =====================================================

        print()
        print("================================")
        print("             SCAN 2")
        print("================================")
        print()

        print(
            "Place the SAME finger again."
        )


        success = (
            self.wait_for_valid_finger(

                FINGERPRINT_CHARBUFFER2,

                30,

                "Place the same finger again."
            )
        )


        if not success:

            print(
                "Second scan timed out."
            )

            self.speak(
                "Second scan failed."
            )

            return False


        print()
        print(
            "Second scan accepted."
        )


        self.speak(
            "Second scan accepted."
        )


        # =====================================================
        # COMPARE
        # =====================================================

        try:

            print()
            print(
                "Comparing both scans..."
            )


            self.speak(
                "Comparing fingerprints."
            )


            accuracy = (
                self.sensor
                .compareCharacteristics()
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
                    "The scans do not match. Please try again."
                )


                self.wait_for_finger_removed()


                return False


            print()
            print(
                "Scans match."
            )


            self.speak(
                "Fingerprints match."
            )


            # =================================================
            # CREATE TEMPLATE
            # =================================================

            print()
            print(
                "Creating fingerprint template..."
            )


            created = (
                self.sensor
                .createTemplate()
            )


            if not created:

                print(
                    "Could not create fingerprint template."
                )

                self.speak(
                    "Could not create the fingerprint."
                )

                self.wait_for_finger_removed()

                return False


            print(
                "Fingerprint template created."
            )


            # =================================================
            # STORE
            # =================================================

            print()
            print(
                "Saving fingerprint using ID:",
                person_id
            )


            stored_id = (
                self.sensor
                .storeTemplate(
                    person_id
                )
            )


            print(
                "Stored fingerprint ID:",
                stored_id
            )


            self.wait_for_finger_removed()


            if stored_id != person_id:

                print()
                print("================================")
                print("        ID MISMATCH")
                print("================================")

                print(
                    "Expected ID:",
                    person_id
                )

                print(
                    "Stored ID:",
                    stored_id
                )

                print("================================")


                self.speak(
                    "Fingerprint ID mismatch."
                )


                return False


            # =================================================
            # SUCCESS
            # =================================================

            print()
            print("================================")
            print(" FINGERPRINT REGISTERED")
            print("================================")

            print(
                "Person ID:",
                person_id
            )


            print(
                "Person Name:",
                person_name
                if person_name
                else "UNKNOWN"
            )


            print(
                "Fingerprint ID:",
                stored_id
            )


            print()
            print(
                "THE IDS ARE THE SAME"
            )

            print("================================")
            print()


            self.speak(
                "Fingerprint registered successfully."
            )


            # =================================================
            # BLUETOOTH REGISTER
            # =================================================

            if person_name:

                message = (
                    "FINGERPRINTREGISTER|"
                    + str(person_id)
                    + "|"
                    + str(person_name)
                )

            else:

                message = (
                    "FINGERPRINTREGISTER|"
                    + str(person_id)
                    + "|UNKNOWN"
                )


            print()
            print("================================")
            print(" FINGERPRINT REGISTER BLUETOOTH")
            print("================================")

            print(
                "SENT:",
                message
            )

            print("================================")
            print()


            bluetooth_success = (
                self.send_bluetooth(
                    message
                )
            )


            print(
                "Bluetooth:",
                bluetooth_success
            )


            return True


        except Exception as error:

            print()
            print("================================")
            print(" FINGERPRINT ENROLLMENT ERROR")
            print("================================")

            print(
                error
            )

            print("================================")
            print()


            self.speak(
                "Fingerprint enrollment failed."
            )


            return False


    # =====================================================
    # LOGIN
    # =====================================================

    def login(
        self,
        person_name=None,
        timeout=30
    ):

        if not self.connected:

            print(
                "Fingerprint sensor is not connected."
            )

            self.speak(
                "Fingerprint sensor is not connected."
            )

            return None


        print()
        print("================================")
        print("       FINGERPRINT LOGIN")
        print("================================")
        print()

        print(
            "WAITING FOR FINGER..."
        )

        print(
            "Place your finger on the sensor."
        )

        print()


        self.speak(
            "Logging in. Place your finger."
        )


        if not self.wait_for_valid_finger(

            FINGERPRINT_CHARBUFFER1,

            timeout,

            "Place your finger."

        ):

            print()
            print(
                "Fingerprint login timed out."
            )


            self.speak(
                "Fingerprint login timed out."
            )


            self.send_bluetooth(
                "LOGIN_FAILED"
            )


            return None


        try:

            print()
            print(
                "Searching fingerprint database..."
            )


            self.speak(
                "Checking fingerprint."
            )


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


            print()
            print(
                "Remove your finger."
            )


            self.wait_for_finger_removed()


            # =================================================
            # NOT RECOGNIZED
            # =================================================

            if position < 0:

                print()
                print("================================")
                print("   FINGERPRINT NOT RECOGNIZED")
                print("================================")
                print()


                self.speak(
                    "Fingerprint not recognized."
                )


                self.send_bluetooth(
                    "LOGIN_FAILED"
                )


                return None


            # =================================================
            # NAME
            # =================================================

            if person_name:

                name = str(
                    person_name
                )

            else:

                name = "UNKNOWN"


            # =================================================
            # SUCCESS
            # =================================================

            print()
            print("================================")
            print("    FINGERPRINT LOGIN SUCCESS")
            print("================================")

            print(
                "Fingerprint ID:",
                position
            )

            print(
                "Name:",
                name
            )

            print(
                "Accuracy:",
                accuracy
            )

            print("================================")
            print()


            self.speak(
                name
                + ", login successful."
            )


            # =================================================
            # BLUETOOTH LOGIN
            # =================================================

            message = (
                "FINGERPRINTLOGIN|"
                + str(position)
                + "|"
                + name
            )


            print()
            print("================================")
            print(" FINGERPRINT LOGIN BLUETOOTH")
            print("================================")

            print(
                "SENT:",
                message
            )

            print("================================")
            print()


            bluetooth_success = (
                self.send_bluetooth(
                    message
                )
            )


            print(
                "Bluetooth:",
                bluetooth_success
            )


            # =================================================
            # RETURN RESULT
            # =================================================

            return {

                "id":
                    position,

                "name":
                    name,

                "accuracy":
                    accuracy
            }


        except Exception as error:

            print()
            print("================================")
            print("   FINGERPRINT LOGIN ERROR")
            print("================================")

            print(
                error
            )

            print("================================")


            self.speak(
                "Fingerprint login failed."
            )


            self.send_bluetooth(
                "LOGIN_FAILED"
            )


            return None


    # =====================================================
    # DELETE
    # =====================================================

    def delete(
        self,
        person_id
    ):

        if not self.connected:

            return False


        if not self.valid_id(
            person_id
        ):

            return False


        try:

            if not self.template_exists(
                person_id
            ):

                print(
                    "No fingerprint found for ID:",
                    person_id
                )

                return False


            self.sensor.deleteTemplate(
                person_id
            )


            print()
            print(
                "Fingerprint deleted:",
                person_id
            )


            self.speak(
                "Fingerprint deleted."
            )


            # =================================================
            # BLUETOOTH DELETE
            # =================================================

            message = (
                "DELETE|"
                + str(person_id)
            )


            print()
            print(
                "SENT:",
                message
            )


            self.send_bluetooth(
                message
            )


            return True


        except Exception as error:

            print(
                "Fingerprint deletion failed:",
                error
            )


            self.speak(
                "Fingerprint deletion failed."
            )


            return False


    # =====================================================
    # CLEAR DATABASE
    # =====================================================

    def clear_database(self):

        if not self.connected:

            raise RuntimeError(
                "Fingerprint sensor is not connected."
            )


        self.sensor.clearDatabase()


        return True


    # =====================================================
    # RESET ALL
    # =====================================================

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


            self.speak(
                "Fingerprint reset cancelled."
            )


            return False


        try:

            self.clear_database()


            print()
            print("================================")
            print(" FINGERPRINT RESET COMPLETE")
            print("================================")

            print(
                "All fingerprint templates were deleted."
            )

            print("================================")
            print()


            self.speak(
                "All fingerprints have been deleted."
            )


            # =================================================
            # BLUETOOTH RESET
            # =================================================

            print(
                "SENT: RESET"
            )


            self.send_bluetooth(
                "RESET"
            )


            return True


        except Exception as error:

            print()
            print(
                "Could not reset fingerprint database:"
            )


            print(
                error
            )


            self.speak(
                "Could not reset the fingerprint database."
            )


            return False


    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.sensor = None

        self.connected = False


        print(
            "Fingerprint sensor closed."
        )
