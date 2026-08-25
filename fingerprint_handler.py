import time

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

            print(
                "================================"
            )
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
            print("AS608 wiring:")
            print("VCC -> Pin 2 (5V)")
            print("GND -> Pin 6 (GND)")
            print("TX  -> Pin 10 (GPIO15 / RXD)")
            print("RX  -> Pin 8  (GPIO14 / TXD)")

            print()
            print(
                "Fingerprint functions will remain"
            )
            print(
                "disabled until the sensor connects."
            )

            print(
                "================================"
            )
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
    # COUNT
    # ============================================================

    def get_count(self):

        if not self.connected:

            return 0

        try:

            return self.sensor.getTemplateCount()

        except Exception:

            return 0


    # ============================================================
    # VALID ID
    # ============================================================

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
            and person_id >= 0
            and person_id < capacity
        )


    # ============================================================
    # WAIT FOR FINGER (WITH DIAGNOSTIC LOGGING)
    # ============================================================

    def wait_for_finger(
        self,
        timeout=30
    ):

        if not self.connected:

            print(
                "[DIAG] wait_for_finger() aborted: "
                "sensor not connected."
            )

            return False

        print()
        print(
            "Place your finger on the sensor..."
        )

        print(
            "[DIAG] Polling readImage() every 0.1s, "
            "timeout =", timeout, "s"
        )

        start = time.time()
        poll_count = 0
        false_count = 0
        error_count = 0

        while (
            time.time() - start
            < timeout
        ):

            poll_count += 1
            elapsed = time.time() - start

            try:

                result = self.sensor.readImage()

            except Exception as error:

                error_count += 1

                print(
                    f"[DIAG] t={elapsed:.1f}s "
                    f"poll#{poll_count} "
                    f"readImage() RAISED -> {error!r} "
                    f"(errors so far: {error_count})"
                )

                # readImage() raises when no finger is present yet.
                # That's the normal "still waiting" state, not a
                # fatal error, so keep polling instead of bailing out.

                time.sleep(0.1)

                continue

            if result:

                print(
                    f"[DIAG] t={elapsed:.1f}s "
                    f"poll#{poll_count} "
                    f"readImage() -> True (finger captured)"
                )

                print(
                    "Fingerprint detected."
                )

                print(
                    f"[DIAG] Summary: {poll_count} polls, "
                    f"{false_count} False reads, "
                    f"{error_count} exceptions before success."
                )

                return True

            false_count += 1

            print(
                f"[DIAG] t={elapsed:.1f}s "
                f"poll#{poll_count} "
                f"readImage() -> False "
                f"(no finger detected yet, "
                f"False count: {false_count})"
            )

            time.sleep(0.1)

        print(
            "Fingerprint timeout."
        )

        print(
            f"[DIAG] Summary: TIMED OUT after {poll_count} polls "
            f"({false_count} False reads, "
            f"{error_count} exceptions). "
            f"If False count is high and never flips to True, "
            f"this points to a physical scan issue: dirty/scratched "
            f"sensor window, finger not covering the full sensor "
            f"area, bright ambient light washing out the optical "
            f"read, or insufficient/sagging VCC. If error_count is "
            f"high instead, check wiring/power stability."
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
    # CHECK TEMPLATE
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

            return self.sensor.loadTemplate(
                template_id,
                FINGERPRINT_CHARBUFFER1
            )

        except Exception:

            return False


    # ============================================================
    # ENROLL
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

            print(
                "Invalid fingerprint ID."
            )

            return False

        print()
        print("================================")
        print("     REGISTER FINGERPRINT")
        print("================================")

        print(
            "Fingerprint ID:",
            person_id
        )


        # --------------------------------------------------------
        # CHECK EXISTING TEMPLATE
        # --------------------------------------------------------

        if self.template_exists(
            person_id
        ):

            print()
            print(
                "This fingerprint ID is already occupied."
            )

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

                self.wait_for_no_finger()

                return False


            # ----------------------------------------------------
            # CHECK IF FINGER ALREADY EXISTS
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

                self.wait_for_no_finger()

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
            # STORE
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
                "Fingerprint ID:",
                person_id
            )

            print(
                "================================"
            )

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
    # LOGIN
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

            print(
                "================================"
            )

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
    # DELETE
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
                    "No fingerprint found for ID:",
                    person_id
                )

                return False


            self.sensor.deleteTemplate(
                person_id
            )

            print(
                "Fingerprint deleted:",
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
    # CLEAR DATABASE
    # ============================================================

    def clear_database(self):

        if not self.connected:

            raise RuntimeError(
                "Fingerprint sensor is not connected."
            )

        self.sensor.clearDatabase()

        return True


    # ============================================================
    # RESET ALL
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

            print(
                "================================"
            )

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
