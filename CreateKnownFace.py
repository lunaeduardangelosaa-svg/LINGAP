import cv2
from camera_handler import CameraHandler


camera = CameraHandler()

camera.start()

print("================================")
print("       FACE CONTROL SYSTEM")
print("================================")
print("E = ENROLL")
print("R = RECOGNIZE")
print("Q = QUIT")
print("================================")


try:

    while camera.running:

        frame = camera.capture()

        if frame is None:
            continue

        if camera.mode == "enroll":

            frame, success, status = camera.enroll(frame)

            if status == "FACE REGISTERED":
                print("Face registered.")

        elif camera.mode == "recognize":

            frame, result = camera.recognize(frame)

            if result is True:
                print("KNOWN FACE")

            elif result is False:
                print("UNKNOWN")

        else:

            cv2.putText(
                frame,
                "E = ENROLL   R = RECOGNIZE   Q = QUIT",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
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

        elif key == ord("q"):

            break

finally:

    camera.stop()
