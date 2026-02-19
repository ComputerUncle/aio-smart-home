from picamera import PiCamera
from time import sleep
def take():
    camera = PiCamera()
    try:
        camera.resolution = (1024, 768)
        sleep(2)  # allow camera to warm up
        camera.capture('../static/image/image.jpg')
        print("Photo saved")
    finally:
        camera.close() 
        print("Camera closed")