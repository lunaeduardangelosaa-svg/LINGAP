import cv2
import pytesseract
import os


class PrescriptionHandler:

    def __init__(self):
        self.image_path = "prescription.jpg"
        self.processed_path = "prescription_processed.jpg"

    def read(self, frame):

        if frame is None:
            return None

        cv2.imwrite(
            self.image_path,
            frame
        )

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        original_text = pytesseract.image_to_string(
            rgb,
            config="--psm 3"
        )

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.resize(
            gray,
            None,
            fx=3,
            fy=3,
            interpolation=cv2.INTER_CUBIC
        )

        gray = cv2.GaussianBlur(
            gray,
            (3, 3),
            0
        )

        processed = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11
        )

        processed = cv2.morphologyEx(
            processed,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(
                cv2.MORPH_RECT,
                (2, 2)
            )
        )

        cv2.imwrite(
            self.processed_path,
            processed
        )

        processed_text = pytesseract.image_to_string(
            processed,
            config="--psm 3"
        )

        original_text = original_text.strip()
        processed_text = processed_text.strip()

        if len(processed_text) > len(original_text):
            return processed_text

        return original_text

    def display(self, text):

        print()
        print("================================")
        print("       PRESCRIPTION")
        print("================================")

        if text:
            print(text)
        else:
            print("No text detected.")

        print("================================")
        print()

    def read_from_camera(self, camera):

        print()
        print("================================")
        print("   PRESCRIPTION READER")
        print("================================")
        print("Place prescription in front of camera.")
        print("SPACE = CAPTURE")
        print("Q = CANCEL")
        print("================================")

        while True:

            frame = camera.capture()

            if frame is None:
                continue

            display = frame.copy()

            height, width = display.shape[:2]

            cv2.rectangle(
                display,
                (40, 90),
                (width - 40, height - 90),
                (0, 255, 255),
                2
            )

            cv2.putText(
                display,
                "PLACE PRESCRIPTION INSIDE BOX",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 255),
                2
            )

            cv2.putText(
                display,
                "SPACE = CAPTURE   Q = CANCEL",
                (50, height - 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            cv2.imshow(
                "Prescription Reader",
                display
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):

                cv2.destroyWindow(
                    "Prescription Reader"
                )

                return None

            if key == 32:
                break

        cv2.destroyWindow(
            "Prescription Reader"
        )

        print()
        print("Capturing prescription...")

        text = self.read(frame)

        self.display(text)

        return text
