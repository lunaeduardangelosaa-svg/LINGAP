import cv2
from camera_handler import CameraHandler
from prescription_handler import PrescriptionHandler


camera = CameraHandler()
prescription = PrescriptionHandler()

camera.start()

print("================================")
print("       FACE CONTROL SYSTEM")
print("================================")
print("E = ENROLL")
print("R = RECOGNIZE")
print("P = PRESCRIPTION")
print("Q = QUIT")
print("================================")


try:

    while camera.running:

        frame = camera.capture()

        if frame is None:
            continue

        if camera.mode == "enroll":

            frame, success, status = camera.enroll(frame)

            if success:
                print("Face registered.")
                camera.set_mode("idle")

        elif camera.mode == "recognize":

            frame, result = camera.recognize(frame)

            if result is True:
                print("KNOWN FACE")

            elif result is False:
                print("UNKNOWN")

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

        key = cv2.waitKey(1) & 0xFF

        if key == ord("e"):

            print("Enrollment mode.")
            camera.set_mode("enroll")

        elif key == ord("r"):

            print("Recognition mode.")
            camera.set_mode("recognize")

        elif key == ord("p"):

            print("Prescription mode.")

            text = prescription.read_from_camera(
                camera
            )

            camera.set_mode("idle")

            print("Returned to main mode.")

        elif key == ord("q"):

            break


finally:

    camera.stop()
