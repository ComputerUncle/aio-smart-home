import cv2
import os
from time import sleep

def take():
    # Create folder if not exists
    os.makedirs("static/image", exist_ok=True)

    # Open default webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Cannot open webcam")
        exit()

    ret, frame = cap.read()  # capture one frame
    if ret:
        filepath = "static/image/image.jpg"
        cv2.imwrite(filepath, frame)
        print(f"Photo saved to {filepath}")
    else:
        print("Failed to capture image")

    cap.release()