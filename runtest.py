from pyfingerprint.pyfingerprint import PyFingerprint
import time

finger = PyFingerprint(
    '/dev/serial0',
    57600,
    0xFFFFFFFF,
    0x00000000
)

print("Connected:", finger.verifyPassword())
print("Put your finger on the sensor...")

while True:
    try:
        result = finger.readImage()
        print("readImage =", result)

        if result:
            print("FINGER DETECTED!")
            break

    except Exception as e:
        print("ERROR:", repr(e))
        break

    time.sleep(0.2)
