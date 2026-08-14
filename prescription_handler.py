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

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.resize(
            gray,
            None,
            fx=2,
            fy=2,
            interpolation=cv2.INTER_CUBIC
        )

        gray = cv2.GaussianBlur(
            gray,
            (3, 3),
            0
        )

        processed = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]

        cv2.imwrite(
            self.processed_path,
            processed
        )

        text = pytesseract.image_to_string(
            processed,
            config="--psm 6"
        )

        return text.strip()

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

    def read_from_camera(self, camera):

        print()
        print("================================")
        print("   PRESCRIPTION READER")
        print("================================")
        print("Place prescription in camera.")
        print("SPACE = capture")
        print("Q = cancel")
        print("================================")

        while True:

            frame = camera.capture()

            if frame is None:
                continue

            display = frame.copy()

            cv2.putText(
                display,
                "PLACE PRESCRIPTION HERE",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )

            cv2.putText(
                display,
                "SPACE = CAPTURE   Q = CANCEL",
                (20, 75),
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

        text = self.read(frame)

        self.display(text)

        return text
