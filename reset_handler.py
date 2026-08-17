import glob
import os


class ResetHandler:

    def __init__(self, fingerprint_handler=None):
        self.fingerprint = fingerprint_handler

    def _delete_file(self, path):
        if not os.path.exists(path):
            return

        try:
            os.remove(path)
            print("Deleted:", path)
        except Exception as error:
            print("Could not delete:", path, error)

    def _delete_directory_files(self, directory):
        if not os.path.exists(directory):
            return

        for file_path in glob.glob(os.path.join(directory, "*")):
            if not os.path.isfile(file_path):
                continue

            try:
                os.remove(file_path)
                print("Deleted:", file_path)
            except Exception as error:
                print("Could not delete:", file_path, error)

    def reset_faces(self):
        self._delete_file("people.pkl")
        self._delete_file("known_face.pkl")

        for file_path in glob.glob("person_*.jpg"):
            self._delete_file(file_path)

        self._delete_file("prescription.jpg")

    def reset_prescriptions(self):
        self._delete_directory_files("prescriptions")

    def reset_fingerprint(self):
        if self.fingerprint is None:
            print("Fingerprint handler is not available.")
            return False

        if not self.fingerprint.is_connected():
            print("Fingerprint sensor is not connected.")
            return False

        try:
            self.fingerprint.clear_database()
            print("Fingerprint database cleared.")
            return True
        except Exception as error:
            print("Could not reset fingerprint database:", error)
            return False

    def reset_all(self):
        print()
        print("================================")
        print("          RESET DATA")
        print("================================")
        print()
        print("WARNING:")
        print("This will permanently delete:")
        print("- All registered faces")
        print("- All face encodings")
        print("- All saved person photos")
        print("- All prescriptions")
        print("- Old face database")
        print("- All fingerprint templates")
        print()
        print("================================")
        print()

        confirmation = input("Type RESET to continue: ").strip()

        if confirmation != "RESET":
            print()
            print("Reset cancelled.")
            print()
            return False

        print()
        print("Starting reset...")
        print()

        self.reset_faces()
        self.reset_prescriptions()
        self.reset_fingerprint()

        print()
        print("================================")
        print("       SYSTEM RESET COMPLETE")
        print("================================")
        print("All registered faces were removed.")
        print("All person photos were removed.")
        print("All prescriptions were removed.")
        print("All fingerprint templates were removed.")
        print()

        return True


if __name__ == "__main__":
    from fingerprint_handler import FingerprintHandler

    fingerprint = FingerprintHandler()

    try:
        ResetHandler(fingerprint).reset_all()
    finally:
        fingerprint.close()
