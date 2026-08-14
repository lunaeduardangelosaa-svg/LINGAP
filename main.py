from camera_handler import CameraHandler
from prescription_handler import PrescriptionHandler


camera = CameraHandler()
prescription = PrescriptionHandler()

camera.start()

while True:

    command = input("> ").lower()

    if command == "e":
        camera.enroll()

    elif command == "r":
        camera.recognize()

    elif command == "p":
        prescription.read_from_camera(camera)

    elif command == "q":
        camera.stop()
        break
