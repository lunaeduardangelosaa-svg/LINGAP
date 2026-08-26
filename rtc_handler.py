import os
import time
import threading
import subprocess
from datetime import datetime

import RPi.GPIO as GPIO


class RTCHandler:

    # ============================================================
    # GPIO
    # ============================================================

    BUZZER_PIN = 26


    # ============================================================
    # INIT
    # ============================================================

    def __init__(
        self,
        prescription_handler
    ):

        self.prescription_handler = (
            prescription_handler
        )

        self.triggered = {}

        self.active_person_id = None

        self.active_person_name = None

        self.active_medicine_name = None


        # ========================================================
        # GPIO SETUP
        # ========================================================

        GPIO.setmode(
            GPIO.BCM
        )

        GPIO.setup(
            self.BUZZER_PIN,
            GPIO.OUT,
            initial=GPIO.LOW
        )

        self.buzzer_on = False


        # ========================================================
        # STOP THREAD
        # ========================================================

        self._stop_thread_flag = False

        self._listener_thread = threading.Thread(
            target=self._listen_for_stop_key,
            daemon=True
        )

        self._listener_thread.start()


    # ============================================================
    # TEXT TO SPEECH
    # ============================================================

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
                    "180",

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


    # ============================================================
    # LISTEN FOR B KEY
    # ============================================================

    def _listen_for_stop_key(
        self
    ):

        while not self._stop_thread_flag:

            try:

                key = input()

            except EOFError:

                break

            except Exception:

                time.sleep(0.1)

                continue


            if key.strip().lower() == "b":

                if self.buzzer_on:

                    self.stop_buzzer()

                    self.active_person_id = None

                    self.active_person_name = None

                    self.active_medicine_name = None

                else:

                    print(
                        "Buzzer is not currently active."
                    )


    # ============================================================
    # CHECK ALL PEOPLE
    # ============================================================

    def check_all_people(
        self,
        people
    ):

        for person in people:

            self.check_person(
                person
            )


    # ============================================================
    # CHECK ONE PERSON
    # ============================================================

    def check_person(
        self,
        person
    ):

        person_id = person.get(
            "id"
        )

        if person_id is None:

            return


        # ========================================================
        # LOAD PRESCRIPTION
        # ========================================================

        data = self.prescription_handler.load(
            person_id
        )

        if not data:

            return


        # ========================================================
        # GET PRESCRIPTION FILE
        # ========================================================

        file_path = (
            self.prescription_handler
            .get_file(
                person_id
            )
        )


        if not os.path.exists(
            file_path
        ):

            return


        # ========================================================
        # PRESCRIPTION START TIME
        # ========================================================

        start_time = os.path.getmtime(
            file_path
        )

        now = time.time()

        elapsed = (
            now
            -
            start_time
        )


        # ========================================================
        # MEDICINES
        # ========================================================

        medicines = data.get(
            "Medicines",
            []
        )


        for index, medicine in enumerate(
            medicines
        ):

            # ====================================================
            # GET HOUR INTERVAL
            # ====================================================

            hour_value = medicine.get(
                "Hour"
            )

            if hour_value is None:

                continue


            try:

                hours = float(
                    hour_value
                )

            except (
                ValueError,
                TypeError
            ):

                continue


            if hours <= 0:

                continue


            # ====================================================
            # CONVERT HOURS TO SECONDS
            # ====================================================

            interval_seconds = (
                hours
                *
                60
                *
                60
            )


            # ====================================================
            # NOT YET TIME
            # ====================================================

            if elapsed < interval_seconds:

                continue


            # ====================================================
            # DETERMINE CURRENT CYCLE
            # ====================================================

            cycle = int(
                elapsed
                /
                interval_seconds
            )


            # ====================================================
            # UNIQUE REMINDER KEY
            # ====================================================

            reminder_key = (

                str(person_id)

                + "_"

                + str(index)
            )


            last_cycle = (
                self.triggered.get(
                    reminder_key,
                    -1
                )
            )


            # ====================================================
            # ALREADY TRIGGERED
            # ====================================================

            if cycle <= last_cycle:

                continue


            self.triggered[
                reminder_key
            ] = cycle


            # ====================================================
            # BUZZER ALREADY ACTIVE
            # ====================================================

            if self.buzzer_on:

                print()

                print(
                    "================================"
                )

                print(
                    "ANOTHER MEDICATION REMINDER"
                )

                print(
                    "================================"
                )

                print(
                    "Person ID:",
                    person_id
                )

                print(
                    "Current active Person ID:",
                    self.active_person_id
                )

                print(
                    "Buzzer is already active."
                )

                print()

                continue


            # ====================================================
            # SET ACTIVE REMINDER
            # ====================================================

            self.active_person_id = (
                person_id
            )

            self.active_person_name = str(
                person.get(
                    "name",
                    "UNKNOWN"
                )
            )

            self.active_medicine_name = str(
                medicine.get(
                    "Name",
                    "medicine"
                )
            )


            # ====================================================
            # PRINT REMINDER
            # ====================================================

            self.print_reminder(

                person,

                medicine,

                hours,

                interval_seconds
            )


            # ====================================================
            # VOICE
            # ====================================================

            self.speak_reminder()


            # ====================================================
            # BUZZER
            # ====================================================

            self.start_buzzer()


    # ============================================================
    # VOICE MEDICATION REMINDER
    # ============================================================

    def speak_reminder(
        self
    ):

        person_name = (
            self.active_person_name
            or
            "Patient"
        )

        medicine_name = (
            self.active_medicine_name
            or
            "medicine"
        )


        def speak():

            for i in range(3):

                try:

                    message = (

                        person_name

                        + ", it is time to take your "

                        + medicine_name
                    )


                    subprocess.run(
                        [
                            "espeak-ng",

                            "-v",
                            "en",

                            "-s",
                            "145",

                            "-p",
                            "45",

                            "-a",
                            "180",

                            message
                        ],

                        stdout=subprocess.DEVNULL,

                        stderr=subprocess.DEVNULL
                    )


                except Exception as error:

                    print(
                        "VOICE ERROR:",
                        error
                    )


                if i < 2:

                    time.sleep(
                        1
                    )


        threading.Thread(
            target=speak,
            daemon=True
        ).start()


    # ============================================================
    # ACKNOWLEDGE MEDICATION
    # ============================================================

    def acknowledge(
        self,
        person_id
    ):

        if not self.buzzer_on:

            print(
                "No active medication reminder."
            )

            return False


        active_id = str(
            self.active_person_id
        )

        scanned_id = str(
            person_id
        )


        # ========================================================
        # WRONG PERSON
        # ========================================================

        if active_id != scanned_id:

            print()

            print(
                "================================"
            )

            print(
                "       WRONG PERSON"
            )

            print(
                "================================"
            )

            print(
                "Medication Person ID:",
                self.active_person_id
            )

            print(
                "Scanned Person ID:",
                person_id
            )

            print()

            print(
                "BUZZER REMAINS ON"
            )

            print(
                "================================"
            )

            print()


            # ----------------------------------------------------
            # VOICE WARNING
            # ----------------------------------------------------

            self.speak(
                "Incorrect person. "
                "Please log in with the correct person."
            )


            return False


        # ========================================================
        # CORRECT PERSON
        # ========================================================

        print()

        print(
            "================================"
        )

        print(
            "    MEDICATION ACKNOWLEDGED"
        )

        print(
            "================================"
        )

        print(
            "Medication Person ID:",
            self.active_person_id
        )

        print(
            "Scanned Person ID:",
            person_id
        )

        print()

        print(
            "Correct person."
        )


        # ========================================================
        # VOICE
        # ========================================================

        self.speak(
            "Medication acknowledged. "
            "You may take your medicine."
        )


        # ========================================================
        # STOP BUZZER
        # ========================================================

        self.stop_buzzer()


        self.active_person_id = None

        self.active_person_name = None

        self.active_medicine_name = None


        print(
            "Medication acknowledged by Person ID:",
            person_id
        )

        print(
            "================================"
        )

        print()


        return True


    # ============================================================
    # CLEAR PERSON TRIGGERS
    # ============================================================

    def clear_triggers_for_person(
        self,
        person_id
    ):

        prefix = (
            str(person_id)
            + "_"
        )


        keys_to_remove = [

            key

            for key in self.triggered

            if key.startswith(
                prefix
            )
        ]


        for key in keys_to_remove:

            del self.triggered[
                key
            ]


    # ============================================================
    # START BUZZER
    # ============================================================

    def start_buzzer(
        self
    ):

        if self.buzzer_on:

            return


        GPIO.output(
            self.BUZZER_PIN,
            GPIO.HIGH
        )


        self.buzzer_on = True


        print()

        print(
            "================================"
        )

        print(
            "        BUZZER ON"
        )

        print(
            "================================"
        )

        print(
            "Medication Person ID:",
            self.active_person_id
        )

        print(
            "Patient:",
            self.active_person_name
        )

        print(
            "Medicine:",
            self.active_medicine_name
        )

        print()

        print(
            "Only this person's ID can stop the buzzer:"
        )

        print(
            self.active_person_id
        )

        print()

        print(
            "Log in with face/fingerprint."
        )

        print(
            "Or press B for manual stop."
        )

        print()


    # ============================================================
    # STOP BUZZER
    # ============================================================

    def stop_buzzer(
        self
    ):

        GPIO.output(
            self.BUZZER_PIN,
            GPIO.LOW
        )


        self.buzzer_on = False


        print(
            "BUZZER STOPPED"
        )


    # ============================================================
    # PRINT REMINDER
    # ============================================================

    def print_reminder(
        self,
        person,
        medicine,
        hours,
        interval_seconds
    ):

        now = datetime.now()


        print()

        print(
            "================================"
        )

        print(
            "       MEDICATION REMINDER"
        )

        print(
            "================================"
        )


        print(
            "TIME:",
            now.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )


        print(
            "PATIENT:",
            person.get(
                "name",
                "UNKNOWN"
            )
        )


        print(
            "PERSON ID:",
            person.get(
                "id",
                "UNKNOWN"
            )
        )


        print()


        print(
            "MEDICINE:",
            medicine.get(
                "Name",
                "UNKNOWN"
            )
        )


        print(
            "INTERVAL:",
            self.format_interval(
                interval_seconds
            )
        )


        print(
            "INSTRUCTIONS:",
            medicine.get(
                "OtherInfo",
                "NOT AVAILABLE"
            )
        )


        print()


        print(
            "================================"
        )

        print(
            "     TIME TO TAKE MEDICINE"
        )

        print(
            "================================"
        )


        print(
            "Log in with face/fingerprint."
        )


        print()


    # ============================================================
    # FORMAT INTERVAL
    # ============================================================

    def format_interval(
        self,
        seconds
    ):

        if seconds < 60:

            return (

                str(
                    round(
                        seconds,
                        2
                    )
                )

                + " seconds"
            )


        if seconds < 3600:

            minutes = (
                seconds
                /
                60
            )


            return (

                str(
                    round(
                        minutes,
                        2
                    )
                )

                + " minutes"
            )


        hours = (
            seconds
            /
            3600
        )


        return (

            str(
                round(
                    hours,
                    2
                )
            )

            + " hours"
        )


    # ============================================================
    # CLEANUP
    # ============================================================

    def cleanup(
        self
    ):

        self._stop_thread_flag = True


        self.stop_buzzer()


        self.active_person_id = None

        self.active_person_name = None

        self.active_medicine_name = None


        GPIO.cleanup(
            self.BUZZER_PIN
        )
