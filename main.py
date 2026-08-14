import cv2

from camera_handler import CameraHandler
from prescription_handler import PrescriptionHandler


camera = CameraHandler()
prescription = PrescriptionHandler(
    api_key="YOUR_API_KEY"
)

camera.start()


try:

    while camera.running:

        frame = camera.capture()

        if frame is None:
            continue

        if camera.mode == "enroll":

            frame, success, status = camera.enroll(frame)

            if success:
                camera.set_mode("idle")

        elif camera.mode == "recognize":

            frame, result = camera.recognize(frame)

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

            camera.set_mode("enroll")

        elif key == ord("r"):

            camera.set_mode("recognize")

        elif key == ord("p"):

            prescription.read_from_camera(
                camera
            )

            camera.set_mode("idle")

        elif key == ord("q"):

            break

finally:

    camera.stop()
