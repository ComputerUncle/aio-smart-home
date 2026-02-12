from picamera import PiCamera
from time import sleep

camera = PiCamera()
camera.resolution = (1024, 768)

sleep(2)  # allow camera to warm up
camera.capture('../image/image.jpg')

print("Photo saved")