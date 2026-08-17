import os
import time
from datetime import datetime

import RPi.GPIO as GPIO


class RTCHandler:

    BUZZER_PIN = 26

    def __init__(self, prescription_handler):

        self.prescription_handler = prescription_handler
        self.triggered = {}

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(
            self.BUZZER_PIN,
            GPIO.OUT,
            initial=GPIO.LOW
        )

        self.buzzer_on = False


    def check_all_people(self, people):

        for person in people:

            self.check_person(person)


    def check_person(self, person):

        person_id = person.get("id")

        if person_id is None:
            return

        data = self.prescription_handler.load(
            person_id
        )

        if not data:
            return

        file_path = self.prescription_handler.get_file(
            person_id
        )

        if not os.path.exists(file_path):
            return

        start_time = os.path.getmtime(
            file_path
        )

        now = time.time()

        elapsed = now - start_time

        medicines = data.get(
            "Medicines",
            []
        )

        for index, medicine in enumerate(
            medicines
        ):

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

            interval_seconds = (
                hours * 60 * 60
            )

            if elapsed < interval_seconds:
                continue

            cycle = int(
                elapsed / interval_seconds
            )

            reminder_key = (
                str(person_id)
                + "_"
                + str(index)
            )

            last_cycle = self.triggered.get(
                reminder_key,
                -1
            )

            if cycle <= last_cycle:
                continue

            self.triggered[
                reminder_key
            ] = cycle

            self.print_reminder(
                person,
                medicine,
                hours,
                interval_seconds
            )

            self.start_buzzer()


    def start_buzzer(self):

        if self.buzzer_on:
            return

        GPIO.output(
            self.BUZZER_PIN,
            GPIO.HIGH
        )

        self.buzzer_on = True

        print(
            "BUZZER ON - PRESS B TO STOP"
        )


    def stop_buzzer(self):

        GPIO.output(
            self.BUZZER_PIN,
            GPIO.LOW
        )

        self.buzzer_on = False

        print(
            "BUZZER STOPPED"
        )


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
            "PRESS B TO STOP BUZZER"
        )
        print()


    def format_interval(
        self,
        seconds
    ):

        if seconds < 60:

            return (
                str(round(seconds, 2))
                + " seconds"
            )

        if seconds < 3600:

            minutes = seconds / 60

            return (
                str(round(minutes, 2))
                + " minutes"
            )

        hours = seconds / 3600

        return (
            str(round(hours, 2))
            + " hours"
        )


    def cleanup(self):

        self.stop_buzzer()

        GPIO.cleanup(
            self.BUZZER_PIN
        )
