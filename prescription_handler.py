import cv2
import json
import os

from google import genai
from google.genai import types


# ============================================
# PRESCRIPTION DIRECTORY
# ============================================

PRESCRIPTION_DIR = "prescriptions"


class PrescriptionHandler:

    def __init__(self):

        # ========================================
        # PUT YOUR NEW GEMINI API KEY HERE
        # ========================================

        api_key = "AQ.Ab8RN6Luuvnoiqf5TLwpnnx0Zt8x7q5d4_CRwXm_IuXg1Dgu6Q"


        if (
            not api_key
            or
            api_key == "PUT_YOUR_NEW_GEMINI_API_KEY_HERE"
        ):

            raise ValueError(
                "Please put your Gemini API key "
                "in prescription_handler.py"
            )


        # ========================================
        # GEMINI
        # ========================================

        self.client = genai.Client(
            api_key=api_key
        )


        self.model = "gemini-3.6-flash"


        # ========================================
        # CREATE DIRECTORY
        # ========================================

        os.makedirs(
            PRESCRIPTION_DIR,
            exist_ok=True
        )


    # ============================================
    # GET FILE FOR PERSON
    # ============================================

    def get_file(
        self,
        person_id
    ):

        return os.path.join(

            PRESCRIPTION_DIR,

            "person_"
            + str(person_id)
            + ".json"
        )


    # ============================================
    # SAVE PRESCRIPTION
    # ============================================

    def save(
        self,
        person_id,
        data
    ):

        file_path = (
            self.get_file(
                person_id
            )
        )


        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(

                data,

                f,

                indent=4,

                ensure_ascii=False
            )


        print()
        print(
            "Prescription saved."
        )
        print(
            "Person ID:",
            person_id
        )
        print(
            "File:",
            file_path
        )
        print()


    # ============================================
    # LOAD PRESCRIPTION
    # ============================================

    def load(
        self,
        person_id
    ):

        file_path = (
            self.get_file(
                person_id
            )
        )


        if not os.path.exists(
            file_path
        ):

            return None


        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)


        except Exception as error:

            print(
                "Prescription load error:",
                error
            )

            return None


    # ============================================
    # DELETE PRESCRIPTION
    # ============================================

    def delete(
        self,
        person_id
    ):

        file_path = (
            self.get_file(
                person_id
            )
        )


        if os.path.exists(
            file_path
        ):

            os.remove(
                file_path
            )

            print(
                "Prescription deleted."
            )


    # ============================================
    # READ IMAGE WITH GEMINI
    # ============================================

    def read(
        self,
        frame
    ):

        if frame is None:

            return None


        image_path = "prescription.jpg"


        # ========================================
        # Picamera2 gives RGB.
        # OpenCV wants BGR for imwrite.
        # ========================================

        bgr = cv2.cvtColor(

            frame,

            cv2.COLOR_RGB2BGR
        )


        success = cv2.imwrite(

            image_path,

            bgr
        )


        if not success:

            print(
                "Could not save prescription image."
            )

            return None


        try:

            print()
            print(
                "================================"
            )
            print(
                "SENDING TO GEMINI"
            )
            print(
                "Please wait..."
            )
            print(
                "================================"
            )


            # ====================================
            # IMAGE
            # ====================================

            with open(
                image_path,
                "rb"
            ) as image_file:

                image_bytes = (
                    image_file.read()
                )


            image_part = (
                types.Part.from_bytes(

                    data=image_bytes,

                    mime_type="image/jpeg"
                )
            )


            # ====================================
            # JSON SCHEMA
            # ====================================

            prescription_schema = {

                "type": "object",

                "properties": {

                    "Patient": {
                        "type": "string"
                    },

                    "Doctor": {
                        "type": "string"
                    },

                    "Age": {
                        "type": "string"
                    },

                    "Sex": {
                        "type": "string"
                    },

                    "Date": {
                        "type": "string"
                    },

                    "Medicines": {

                        "type": "array",

                        "items": {

                            "type": "object",

                            "properties": {

                                "Name": {
                                    "type": "string"
                                },

                                "Hour": {
                                    "type": "number"
                                },

                                "OtherInfo": {
                                    "type": "string"
                                }
                            },

                            "required": [
                                "Name",
                                "Hour",
                                "OtherInfo"
                            ]
                        }
                    }
                },

                "required": [
                    "Patient",
                    "Doctor",
                    "Age",
                    "Sex",
                    "Date",
                    "Medicines"
                ]
            }


            # ====================================
            # PROMPT
            # ====================================

            prompt = """
Read this prescription image.

Extract ONLY information that is actually
visible in the prescription.

Return JSON matching the provided schema.

Patient:
Patient name.

Doctor:
Doctor name.

Age:
Patient age.

Sex:
Patient sex.

Date:
Prescription date.

Medicines:
Every medicine visible.

For each medicine:

Name:
Exact medicine name when readable.

Hour:
The frequency or schedule, num hour

Examples:

OtherInfo:
Everything else visible about that medicine,
such as:

- strength
- dosage
- number of tablets
- mL
- before meals
- after meals
- duration
- special instructions

RULES:

Do not invent information.

Do not guess.

If something is not visible:
"NOT VISIBLE"

If handwriting is unclear:
"UNCLEAR"

Do not diagnose.

Do not recommend medication.

Do not provide medical advice.

This is ONLY transcription and data extraction.
"""


            # ====================================
            # GEMINI
            # ====================================

            response = (
                self.client.models.generate_content(

                    model=self.model,

                    contents=[
                        image_part,
                        prompt
                    ],

                    config=types.GenerateContentConfig(

                        response_mime_type="application/json",

                        response_json_schema=(
                            prescription_schema
                        )
                    )
                )
            )


            # ====================================
            # RESPONSE
            # ====================================

            text = response.text


            if not text:

                print(
                    "Gemini returned no text."
                )

                return None


            # ====================================
            # JSON
            # ====================================

            data = json.loads(
                text
            )


            return data


        except json.JSONDecodeError as error:

            print(
                "JSON ERROR:",
                error
            )

            return None


        except Exception as error:

            print()
            print(
                "================================"
            )
            print(
                "GEMINI ERROR"
            )
            print(
                "================================"
            )
            print(
                error
            )
            print(
                "================================"
            )

            return None


    # ============================================
    # DISPLAY PRESCRIPTION
    # ============================================

    def display(
        self,
        data
    ):

        print()
        print(
            "================================"
        )
        print(
            "          PRESCRIPTION"
        )
        print(
            "================================"
        )


        if not data:

            print(
                "NO PRESCRIPTION"
            )

            print(
                "================================"
            )

            return


        print(
            "Patient:",
            data.get(
                "Patient",
                "NOT VISIBLE"
            )
        )


        print(
            "Doctor:",
            data.get(
                "Doctor",
                "NOT VISIBLE"
            )
        )


        print(
            "Age:",
            data.get(
                "Age",
                "NOT VISIBLE"
            )
        )


        print(
            "Sex:",
            data.get(
                "Sex",
                "NOT VISIBLE"
            )
        )


        print(
            "Date:",
            data.get(
                "Date",
                "NOT VISIBLE"
            )
        )


        print()
        print(
            "MEDICINES:"
        )


        medicines = data.get(
            "Medicines",
            []
        )


        for index, medicine in enumerate(

            medicines,

            start=1
        ):

            print()
            print(
                "Medicine",
                index
            )

            print(
                "  Name:",
                medicine.get(
                    "Name",
                    "NOT VISIBLE"
                )
            )

            print(
                "  Hour:",
                medicine.get(
                    "Hour",
                    "NOT VISIBLE"
                )
            )

            print(
                "  Other Info:",
                medicine.get(
                    "OtherInfo",
                    "NOT VISIBLE"
                )
            )


        print()
        print(
            "================================"
        )


    # ============================================
    # CAMERA READER
    # ============================================

    def read_from_camera(
        self,
        camera
    ):

        print()
        print(
            "================================"
        )
        print(
            "       PRESCRIPTION READER"
        )
        print(
            "================================"
        )
        print(
            "Place prescription inside the box."
        )
        print()
        print(
            "SPACE = CAPTURE"
        )
        print(
            "Q = CANCEL"
        )
        print(
            "================================"
        )


        captured_frame = None


        while True:

            frame = camera.capture()


            if frame is None:

                continue


            display = frame.copy()


            height, width = (
                display.shape[:2]
            )


            # =================================
            # BOX
            # =================================

            cv2.rectangle(

                display,

                (40, 90),

                (
                    width - 40,
                    height - 90
                ),

                (0, 255, 255),

                2
            )


            # =================================
            # TEXT
            # =================================

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


            key = (
                cv2.waitKey(1) &
                0xFF
            )


            # =================================
            # CANCEL
            # =================================

            if key == ord("q"):

                cv2.destroyWindow(
                    "Prescription Reader"
                )

                return None


            # =================================
            # CAPTURE
            # =================================

            if key == 32:

                captured_frame = (
                    frame.copy()
                )

                break


        cv2.destroyWindow(
            "Prescription Reader"
        )


        # ========================================
        # GEMINI
        # ========================================

        data = self.read(
            captured_frame
        )


        # ========================================
        # DISPLAY
        # ========================================

        self.display(
            data
        )


        return data
