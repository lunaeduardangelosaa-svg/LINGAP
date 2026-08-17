import time
import os
import sys

from pyfingerprint.pyfingerprint import (
    PyFingerprint,
    FINGERPRINT_CHARBUFFER1,
    FINGERPRINT_CHARBUFFER2
)


class FingerprintHandler:

    def __init__(
        self,
        port="/dev/serial0",
        baudrate=57600,
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


    # ============================================================
    # CONNECT
    # ============================================================

    def connect(self):

        try:

            print()
            print("================================")
            print("     FINGERPRINT SENSOR")
            print("================================")

            print("Port:", self.port)
            print("Baudrate:", self.baudrate)

            self.sensor = PyFingerprint(
                self.port,
                self.baudrate,
                self.address,
                self.password
            )

            if not self.sensor.verifyPassword():

                raise Exception(
                    "Incorrect fingerprint sensor password."
                )

            self.connected = True

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
            print("Check:")
            print("VCC  -> Pin 2 (5V)")
            print("GND  -> Pin 6")
            print("TX   -> Pin 10 (GPIO15 RXD)")
            print("RX   -> Pin 8 (GPIO14 TXD)")
            print()
            print("================================")
            print()

            return False


    # ============================================================
    # STATUS
    # ============================================================

    def is_connected(self):

        return self.connected


    # ============================================================
    # CAPACITY
    # ============================================================

    def get_capacity(self):

        if not self.connected:

            return 0

        try:

            return self.sensor.getStorageCapacity()

        except Exception:

            return 0


    # ============================================================
    # STORED COUNT
    # ============================================================

    def get_count(self):

        if not self.connected:

            return 0

        try:

            return self.sensor.getTemplateCount()

        except Exception:

            return 0


    # ============================================================
    # CHECK WHETHER TEMPLATE ID IS VALID
    # ============================================================

    def valid_id(self, person_id):

        if not self.connected:

            return False

        capacity = self.get_capacity()

        return (
            isinstance(person_id, int)
            and person_id >= 0
            and person_id < capacity
        )


    # ============================================================
    # WAIT FOR FINGER
    # ============================================================

    def wait_for_finger(
        self,
        timeout=30
    ):

        if not self.connected:

            return False

        print()
        print("Place your finger on the sensor...")

        start = time.time()

        while (
            time.time() - start
            < timeout
        ):

            try:

                if self.sensor.readImage():

                    print(
                        "Fingerprint detected."
                    )

                    return True

            except Exception as error:

                print(
                    "Fingerprint read error:",
                    error
                )

                return False

            time.sleep(0.1)

        print(
            "Fingerprint timeout."
        )

        return False


    # ============================================================
    # WAIT FOR FINGER REMOVAL
    # ============================================================

    def wait_for_no_finger(
        self,
        timeout=10
    ):

        if not self.connected:

            return False

        print(
            "Remove your finger..."
        )

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


    # ============================================================
    # CHECK IF FINGERPRINT ID ALREADY EXISTS
    # ============================================================

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

            # loadTemplate returns True when
            # a template exists in the requested slot.

            return self.sensor.loadTemplate(
                template_id,
                FINGERPRINT_CHARBUFFER1
            )

        except Exception:

            return False


    # ============================================================
    # ENROLL FINGERPRINT
    # ============================================================

    def enroll(
        self,
        person_id
    ):

        if not self.connected:

            print(
                "Fingerprint sensor is not connected."
            )

            return False

        if not self.valid_id(
            person_id
        ):

            print()
            print(
                "Invalid fingerprint ID."
            )

            print(
                "Fingerprint ID must be between 0 and",
                self.get_capacity() - 1
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

        # --------------------------------------------------------
        # CHECK WHETHER SLOT IS ALREADY USED
        # --------------------------------------------------------

        if self.template_exists(
            person_id
        ):

            print()
            print(
                "This person already has a fingerprint."
            )

            print(
                "Fingerprint ID:",
                person_id
            )

            print("================================")

            return False

        # --------------------------------------------------------
        # FIRST SCAN
        # --------------------------------------------------------

        print()
        print(
            "STEP 1"
        )

        if not self.wait_for_finger():

            return False

        try:

            if not self.sensor.convertImage(
                FINGERPRINT_CHARBUFFER1
            ):

                print(
                    "Could not process first fingerprint."
                )

                return False

            # ----------------------------------------------------
            # CHECK IF THIS FINGER IS ALREADY REGISTERED
            # ----------------------------------------------------

            try:

                position, accuracy = (
                    self.sensor.searchTemplate()
                )

                if position >= 0:

                    print()
                    print(
                        "This fingerprint is already registered."
                    )

                    print(
                        "Existing fingerprint ID:",
                        position
                    )

                    print(
                        "Accuracy:",
                        accuracy
                    )

                    self.wait_for_no_finger()

                    return False

            except Exception:

                pass

            self.wait_for_no_finger()

            # ----------------------------------------------------
            # SECOND SCAN
            # ----------------------------------------------------

            print()
            print(
                "STEP 2"
            )

            print(
                "Place the SAME finger again."
            )

            if not self.wait_for_finger():

                return False

            if not self.sensor.convertImage(
                FINGERPRINT_CHARBUFFER2
            ):

                print(
                    "Could not process second fingerprint."
                )

                return False

            # ----------------------------------------------------
            # CREATE TEMPLATE
            # ----------------------------------------------------

            print(
                "Creating fingerprint template..."
            )

            if not self.sensor.createTemplate():

                print()
                print(
                    "The two fingerprint scans "
                    "did not match."
                )

                self.wait_for_no_finger()

                return False

            # ----------------------------------------------------
            # STORE TEMPLATE
            # ----------------------------------------------------

            print(
                "Saving fingerprint..."
            )

            self.sensor.storeTemplate(
                person_id
            )

            self.wait_for_no_finger()

            print()
            print("================================")
            print(" FINGERPRINT REGISTERED")
            print("================================")

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

            return True

        except Exception as error:

            print()
            print(
                "Fingerprint enrollment failed:"
            )

            print(
                error
            )

            self.wait_for_no_finger()

            return False


    # ============================================================
    # FINGERPRINT LOGIN
    # ============================================================

    def login(
        self,
        timeout=30
    ):

        if not self.connected:

            print(
                "Fingerprint sensor is not connected."
            )

            return None

        print()
        print("================================")
        print("       FINGERPRINT LOGIN")
        print("================================")

        if not self.wait_for_finger(
            timeout
        ):

            return None

        try:

            if not self.sensor.convertImage(
                FINGERPRINT_CHARBUFFER1
            ):

                print(
                    "Could not process fingerprint."
                )

                self.wait_for_no_finger()

                return None

            position, accuracy = (
                self.sensor.searchTemplate()
            )

            self.wait_for_no_finger()

            if position < 0:

                print()
                print("================================")
                print("   FINGERPRINT NOT RECOGNIZED")
                print("================================")
                print()

                return None

            print()
            print("================================")
            print("    FINGERPRINT LOGIN OK")
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
                "id": position,
                "accuracy": accuracy
            }

        except Exception as error:

            print(
                "Fingerprint login error:",
                error
            )

            self.wait_for_no_finger()

            return None


    # ============================================================
    # DELETE ONE FINGERPRINT
    # ============================================================

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
                    "No fingerprint found for Person ID:",
                    person_id
                )

                return False

            self.sensor.deleteTemplate(
                person_id
            )

            print(
                "Fingerprint deleted for Person ID:",
                person_id
            )

            return True

        except Exception as error:

            print(
                "Fingerprint deletion failed:",
                error
            )

            return False


    # ============================================================
    # CLEAR ALL FINGERPRINT DATA
    # ============================================================

    def clear_database(self):

        if not self.connected:
            raise RuntimeError(
                "Fingerprint sensor is not connected."
            )

        self.sensor.clearDatabase()

        return True


    # ============================================================
    # RESET ALL FINGERPRINT DATA
    # ============================================================

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
            print(
                "All fingerprint templates were deleted."
            )
            print("================================")
            print()

            return True

        except Exception as error:

            print(
                "Could not reset fingerprint database:"
            )

            print(
                error
            )

            return False


    # ============================================================
    # CLOSE
    # ============================================================

    def close(self):

        self.sensor = None
        self.connected = False

        print(
            "Fingerprint sensor closed."
        )


# =================================================================
# STANDALONE TEST
# =================================================================
