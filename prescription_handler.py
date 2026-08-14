import cv2
import requests


class PrescriptionHandler:

    def __init__(self, api_key):
        self.api_url = "https://api.ocr.space/parse/image"
        self.api_key = api_key
        self.image_path = "prescription.jpg"

    def read(self, frame):

        if frame is None:
            return None

        cv2.imwrite(
            self.image_path,
            frame
        )

        try:

            with open(
                self.image_path,
                "rb"
            ) as image_file:

                response = requests.post(
                    self.api_url,
                    files={
                        "file": image_file
                    },
                    data={
                        "apikey": self.api_key,
                        "language": "eng",
                        "isOverlayRequired": "false",
                        "detectOrientation": "true",
                        "scale": "true",
                        "OCREngine": "2"
                    },
                    timeout=60
                )

            if response.status_code != 200:
                print(
                    "OCR HTTP ERROR:",
                    response.status_code
                )
                return None

            result = response.json()

            if result.get("IsErroredOnProcessing"):

                errors = result.get(
                    "ErrorMessage",
                    "Unknown OCR error"
                )

                if isinstance(errors, list):
                    errors = " ".join(
                        str(error)
                        for error in errors
                    )

                print(
                    "OCR ERROR:",
                    errors
                )

                return None

            parsed_results = result.get(
                "ParsedResults",
                []
            )

            if not parsed_results:
                print("OCR returned no results.")
                return None

            text_parts = []

            for item in parsed_results:

                text = item.get(
                    "ParsedText",
                    ""
                )

                if text.strip():
                    text_parts.append(
                        text.strip()
                    )

            if not text_parts:
                print("No text detected.")
                return None

            return "\n".join(text_parts)

        except requests.RequestException as error:

            print(
                "OCR CONNECTION ERROR:",
                error
            )

            return None

        except Exception as error:

            print(
                "OCR ERROR:",
                error
            )

            return None

    def display(self, text):

        print()
        print("================================")
        print("       PRESCRIPTION")
        print("================================")

        if text:
            print(text)
        else:
            print("NO TEXT DETECTED")

        print("================================")
        print()

    def read_from_camera(self, camera):

        print()
        print("================================")
        print("   PRESCRIPTION READER")
        print("================================")
        print("Place prescription inside the box.")
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
        print("Sending image to OCR.space...")

        text = self.read(frame)

        self.display(text)

        return text
