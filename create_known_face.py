import face_recognition
import pickle

image = face_recognition.load_image_file("known_face.jpg")
faces = face_recognition.face_encodings(image)

if len(faces) == 0:
    print("NO FACE FOUND")
else:
    data = {
        "names": ["Eduard"],
        "encodings": [faces[0]]
    }

    with open("known_face.pkl", "wb") as f:
        pickle.dump(data, f)

    print("DONE! known_face.pkl created")
