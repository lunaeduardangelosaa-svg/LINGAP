import cv2

from camera_handler import CameraHandler
from prescription_handler import PrescriptionHandler
from rtc_handler import RTCHandler
from fingerprint_handler import FingerprintHandler
from reset_handler import ResetHandler
from system_handler import SystemHandler


camera = CameraHandler()
prescription = PrescriptionHandler()
rtc = RTCHandler(prescription)
fingerprint = FingerprintHandler()
reset_handler = ResetHandler(fingerprint)

system = SystemHandler(
    camera,
    prescription,
    fingerprint,
    reset_handler,
    rtc
)

camera.start()

print()
print("================================")
print("          LINGAP SYSTEM")
print("================================")
print("F = ENROLL FINGERPRINT")
print("G = FINGERPRINT LOGIN")
print("H = RESET ALL DATA")
print("E = ENROLL FACE")
print("R = RECOGNIZE FACE")
print("P = ADD PRESCRIPTION")
print("L = LIST PEOPLE")
print("Q = QUIT")
print("================================")
print()

try:
    while camera.running:
        frame = camera.capture()

        if frame is None:
            continue

        frame = system.process_frame(frame)

        cv2.imshow(
            "Face System",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        if system.handle_key(key):
            break

finally:
    camera.stop()
    fingerprint.close()
    cv2.destroyAllWindows()
    print("System stopped.")
