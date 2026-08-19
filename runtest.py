from pyfingerprint.pyfingerprint import PyFingerprint
import time

# ============================================================
# AS608 CONFIGURATION
# ============================================================

PORT = '/dev/serial0'
BAUDRATE = 57600
ADDRESS = 0xFFFFFFFF
PASSWORD = 0x00000000


# ============================================================
# CONNECT TO FINGERPRINT SENSOR
# ============================================================

print("=" * 50)
print("AS608 FINGERPRINT TEST")
print("=" * 50)

try:
    finger = PyFingerprint(
        PORT,
        BAUDRATE,
        ADDRESS,
        PASSWORD
    )

    if not finger.verifyPassword():
        print("❌ Fingerprint password verification failed.")
        raise Exception("Invalid fingerprint sensor password")

    print("✅ Fingerprint sensor connected!")
    print("Port:", PORT)
    print("Baudrate:", BAUDRATE)
    print("Capacity:", finger.getStorageCapacity())
    print("")

except Exception as e:
    print("=" * 50)
    print("❌ FINGERPRINT CONNECTION FAILED")
    print("=" * 50)
    print("Exception:", repr(e))
    print("Port:", PORT)
    print("Baudrate:", BAUDRATE)
    raise SystemExit


# ============================================================
# MAIN FINGERPRINT LOOP
# ============================================================

print("=" * 50)
print("READY")
print("Place your finger on the AS608...")
print("=" * 50)

while True:

    try:

        # ----------------------------------------------------
        # STEP 1: GET FINGER IMAGE
        # Equivalent to:
        # finger.getImage()
        # ----------------------------------------------------

        image = finger.readImage()

        if not image:
            print("Waiting for finger...", end="\r")
            time.sleep(0.2)
            continue

        print("\n")
        print("✅ FINGER DETECTED!")
        print("Image captured successfully.")

        # ----------------------------------------------------
        # STEP 2: CONVERT IMAGE TO TEMPLATE
        # Equivalent to:
        # finger.image2Tz()
        # ----------------------------------------------------

        print("Converting fingerprint image...")

        converted = finger.convertImage(0x01)

        if not converted:
            print("❌ Could not convert fingerprint image.")
            print("Try placing your finger flat and steady.")
            print("")
            time.sleep(1)
            continue

        print("✅ Image converted.")

        # ----------------------------------------------------
        # STEP 3: SEARCH DATABASE
        # Equivalent to:
        # finger.fingerFastSearch()
        # ----------------------------------------------------

        print("Searching fingerprint database...")

        result = finger.searchTemplate()

        position = result[0]
        score = result[1]

        if position >= 0:

            print("=" * 50)
            print("✅ FINGERPRINT MATCH!")
            print("Fingerprint ID:", position)
            print("Match score:", score)
            print("=" * 50)

        else:

            print("=" * 50)
            print("❌ FINGERPRINT NOT REGISTERED")
            print("Search result:", result)
            print("=" * 50)

        # ----------------------------------------------------
        # WAIT FOR FINGER TO BE REMOVED
        # ----------------------------------------------------

        print("Remove finger...")

        while True:
            try:
                if not finger.readImage():
                    break
            except:
                break

            time.sleep(0.2)

        print("Finger removed.")
        print("")
        print("Place your finger on the AS608...")

    except Exception as e:

        print("\n")
        print("=" * 50)
        print("❌ FINGERPRINT ERROR")
        print("=" * 50)
        print("Exception type:", type(e).__name__)
        print("Exception:", repr(e))
        print("=" * 50)

        time.sleep(1)
