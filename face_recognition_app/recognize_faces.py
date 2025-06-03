import face_recognition
import cv2
import os
import numpy as np
import threading
import time
from logger import log_attendance  # Excel log funksiyasi

oquvhci = 0

KNOWN_FACES_DIR = "known_faces"
TOLERANCE = 0.5
MODEL = "hog"
FRAME_INTERVAL = 10

print("[INFO] Yuzlarni yuklash...")

known_faces = []
known_names = []

for class_name in os.listdir(KNOWN_FACES_DIR):
    class_path = os.path.join(KNOWN_FACES_DIR, class_name)
    if not os.path.isdir(class_path):
        continue
    for student_name in os.listdir(class_path):
        student_path = os.path.join(class_path, student_name)
        if not os.path.isdir(student_path):
            continue
        for filename in os.listdir(student_path):
            image_path = os.path.join(student_path, filename)
            try:
                image = face_recognition.load_image_file(image_path)
                encoding = face_recognition.face_encodings(image)
                if encoding:
                    known_faces.append(encoding[0])
                    known_names.append(f"{class_name}_{student_name}")
            except Exception as e:
                print(f"[ERROR] Failed to process {image_path}: {e}")

class VideoCaptureThreaded:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.ret, self.frame = self.cap.read()
        self.running = True
        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()

    def update(self):
        while self.running:
            self.ret, self.frame = self.cap.read()

    def read(self):
        return self.ret, self.frame

    def release(self):
        self.running = False
        self.thread.join()
        self.cap.release()

print("[INFO] Kamera ishga tushirildi...")
video = VideoCaptureThreaded(0)

frame_count = 0
fps_time = time.time()
fps = 0

while True:
    ret, frame = video.read()
    if not ret:
        break

    frame_count += 1
    process_this_frame = (frame_count % FRAME_INTERVAL == 0)

    if process_this_frame:
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame, model=MODEL)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_faces, face_encoding, TOLERANCE)
            name = "Begona"

            if True in matches:
                match_index = np.argmin(face_recognition.face_distance(known_faces, face_encoding))
                name = known_names[match_index]

                # Excelga yozish
                class_name, student_name = name.split("_", 1)
                log_attendance(student_name, class_name)

            face_names.append(name)

    if 'face_locations' in locals():
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            color = (0, 255, 0) if name != "Begona" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

    elapsed = time.time() - fps_time
    if elapsed >= 1.0:
        fps = frame_count / elapsed
        frame_count = 0
        fps_time = time.time()

    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow("Yuzni aniqlash", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

video.release()
cv2.destroyAllWindows()