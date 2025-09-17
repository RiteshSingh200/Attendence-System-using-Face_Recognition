import cv2
import numpy as np
import os

dataset_dir = "dataset"

def capture_faces(name):
    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(0)

    count = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            count += 1
            cv2.imwrite(f"{dataset_dir}/{name}_{count}.jpg", gray[y:y+h, x:x+w])
            cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
            cv2.imshow("Capturing Faces", frame)

        if cv2.waitKey(1) & 0xFF == ord('q') or count >= 50:
            break

    cap.release()
    cv2.destroyAllWindows()

def train_model():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    faces, ids, names = [], [], []
    for file in os.listdir(dataset_dir):
        if file.endswith(".jpg"):
            path = os.path.join(dataset_dir, file)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            name = file.split("_")[0]
            if name not in names:
                names.append(name)
            label_id = names.index(name)
            faces.append(img)
            ids.append(label_id)

    if faces:
        recognizer.train(faces, np.array(ids))
        recognizer.save("face_model.yml")
        np.save("names.npy", names)
        print("✅ Training complete. Model saved!")
    else:
        print("⚠️ No face images found in dataset folder!")

if __name__ == "__main__":
    person_name = input("Enter employee name for dataset capture: ")
    print("Be infront of camera, capturing images")
    capture_faces(person_name)
    train_model()
