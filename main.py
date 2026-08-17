import cv2
import sys
import os
import glob

from camera_handler import CameraHandler
from prescription_handler import PrescriptionHandler
from rtc_handler import RTCHandler


def reset_system():

    print()
    print("================================")
    print("       RESET FACE SYSTEM")
    print("================================")
    print()
    print("WARNING:")
    print("This will permanently delete:")
    print()
    print("- All registered people")
    print("- All face encodings")
    print("- All saved person photos")
    print("- All prescriptions")
    print("- Old face database")
    print()
    print("================================")
    print()

    confirm = input(
        "Type RESET to continue: "
    ).strip()

    if confirm != "RESET":

        print()
        print("Reset cancelled.")
        print()

        return

    print()
    print("Starting reset...")
    print()

    if os.path.exists("people.pkl"):

        try:

            os.remove(
                "people.pkl"
            )

            print(
                "Deleted people.pkl"
            )

        except Exception as error:

            print(
                "Could not delete people.pkl:",
                error
            )

    if os.path.exists("known_face.pkl"):

        try:

            os.remove(
                "known_face.pkl"
            )

            print(
                "Deleted known_face.pkl"
            )

        except Exception as error:

            print(
                "Could not delete known_face.pkl:",
                error
            )

    person_photos = glob.glob(
        "person_*.jpg"
    )

    for file_path in person_photos:

        try:

            os.remove(
                file_path
            )

            print(
                "Deleted:",
                file_path
            )

        except Exception as error:

            print(
                "Could not delete:",
                file_path,
                error
            )

    prescription_dir = "prescriptions"

    if os.path.exists(
        prescription_dir
    ):

        prescription_files = glob.glob(
            os.path.join(
                prescription_dir,
                "*"
            )
        )

        for file_path in prescription_files:

            if os.path.isfile(
                file_path
            ):

                try:

                    os.remove(
                        file_path
                    )

                    print(
                        "Deleted:",
                        file_path
                    )

                except Exception as error:

                    print(
                        "Could not delete:",
                        file_path,
                        error
                    )

    if os.path.exists(
        "prescription.jpg"
    ):

        try:

            os.remove(
                "prescription.jpg"
            )

            print(
                "Deleted prescription.jpg"
            )

        except Exception as error:

            print(
                "Could not delete prescription.jpg:",
                error
            )

    print()
    print("================================")
    print("       SYSTEM RESET COMPLETE")
    print("================================")
    print()
    print("All registered faces were removed.")
    print("All person photos were removed.")
    print("All prescriptions were removed.")
    print()


if len(sys.argv) > 1:

    command = sys.argv[1].lower()

    if command == "reset":

        reset_system()

        sys.exit(0)

    print()
    print(
        "Unknown command:",
        sys.argv[1]
    )
    print()
    print("Available commands:")
    print()
    print("python main.py")
    print("python main.py reset")
    print()

    sys.exit(1)


camera = CameraHandler()

prescription = PrescriptionHandler()

rtc = RTCHandler(
    prescription
)

camera.start()

last_person_id = None

print()
print(
    "================================"
)
print(
    "       FACE CONTROL SYSTEM"
)
print(
    "================================"
)
print(
    "E = ENROLL NEW PERSON"
)
print(
    "R = RECOGNIZE"
)
print(
    "P = ADD PRESCRIPTION TO PERSON"
)
print(
    "L = LIST PEOPLE"
)
print(
    "Q = QUIT"
)
print(
    "================================"
)
print()


try:

    while camera.running:

        frame = camera.capture()

        if frame is None:

            continue

        rtc.check_all_people(
            camera.get_people()
        )

        if camera.mode == "enroll":

            frame, success, status = (
                camera.enroll(
                    frame
                )
            )

            if success:

                camera.set_mode(
                    "idle"
                )

        elif camera.mode == "recognize":

            frame, person = (
                camera.recognize(
                    frame
                )
            )

            if person is not None:

                person_id = (
                    person["id"]
                )

                if (
                    person_id !=
                    last_person_id
                ):

                    last_person_id = (
                        person_id
                    )

                    print()
                    print(
                        "================================"
                    )
                    print(
                        "       PERSON RECOGNIZED"
                    )
                    print(
                        "================================"
                    )
                    print(
                        "ID:",
                        person["id"]
                    )
                    print(
                        "Name:",
                        person["name"]
                    )

                    data = (
                        prescription.load(
                            person_id
                        )
                    )

                    if data is not None:

                        print()
                        print(
                            "Prescription found."
                        )

                        prescription.display(
                            data
                        )

                    else:

                        print()
                        print(
                            "NO PRESCRIPTION "
                            "ASSIGNED"
                        )

                    print(
                        "================================"
                    )

            else:

                last_person_id = None

        else:

            cv2.putText(
                frame,
                "E ENROLL | R RECOGNIZE | P PRESCRIPTION | Q QUIT",
                (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (255, 255, 255),
                2
            )

        cv2.imshow(
            "Face System",
            frame
        )

        key = (
            cv2.waitKey(1) &
            0xFF
        )

        if key == ord("e"):

            print()
            print(
                "Enrollment mode."
            )
            print(
                "Look at the camera."
            )

            camera.set_mode(
                "enroll"
            )

        elif key == ord("r"):

            print()
            print(
                "Recognition mode."
            )

            last_person_id = None

            camera.set_mode(
                "recognize"
            )

        elif key == ord("p"):

            people = (
                camera.get_people()
            )

            print()
            print(
                "================================"
            )
            print(
                "       ASSIGN PRESCRIPTION"
            )
            print(
                "================================"
            )

            if not people:

                print(
                    "No people registered."
                )

                continue

            for person in people:

                print(
                    str(person["id"])
                    + " = "
                    + person["name"]
                )

            print(
                "================================"
            )

            choice = input(
                "Enter Person ID: "
            ).strip()

            try:

                person_id = int(
                    choice
                )

            except ValueError:

                print(
                    "Invalid Person ID."
                )

                continue

            person = (
                camera.get_person(
                    person_id
                )
            )

            if person is None:

                print(
                    "Person not found."
                )

                continue

            print()
            print(
                "Assigning prescription to:"
            )
            print(
                "ID:",
                person["id"]
            )
            print(
                "Name:",
                person["name"]
            )
            print()

            confirm = input(
                "Continue? Y/N: "
            ).strip().lower()

            if confirm != "y":

                print(
                    "Cancelled."
                )

                continue

            camera.set_mode(
                "idle"
            )

            data = (
                prescription.read_from_camera(
                    camera
                )
            )

            if data is not None:

                prescription.save(
                    person_id,
                    data
                )

                print()
                print(
                    "================================"
                )
                print(
                    "PRESCRIPTION ASSIGNED"
                )
                print(
                    "================================"
                )
                print(
                    "Person:",
                    person["name"]
                )
                print(
                    "Person ID:",
                    person_id
                )
                print(
                    "================================"
                )

            else:

                print(
                    "No prescription was saved."
                )

            camera.set_mode(
                "idle"
            )

        elif key == ord("l"):

            people = (
                camera.get_people()
            )

            print()
            print(
                "================================"
            )
            print(
                "       REGISTERED PEOPLE"
            )
            print(
                "================================"
            )

            if not people:

                print(
                    "No people registered."
                )

            else:

                for person in people:

                    person_id = (
                        person["id"]
                    )

                    name = (
                        person["name"]
                    )

                    data = (
                        prescription.load(
                            person_id
                        )
                    )

                    if data:

                        prescription_status = (
                            "PRESCRIPTION: YES"
                        )

                    else:

                        prescription_status = (
                            "PRESCRIPTION: NO"
                        )

                    print()
                    print(
                        "ID:",
                        person_id
                    )
                    print(
                        "Name:",
                        name
                    )
                    print(
                        prescription_status
                    )

            print()
            print(
                "================================"
            )

        elif key == ord("q"):

            print()
            print(
                "Shutting down..."
            )

            break

finally:

    camera.stop()

    cv2.destroyAllWindows()

    print(
        "System stopped."
    )
