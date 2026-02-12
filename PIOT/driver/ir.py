
import RPi.GPIO as GPIO

def init():
    GPIO.setup(17, GPIO.IN)  # set GPIO 17 as input


def get_ir_sensor_state():

    ret = False

    # Object is detected
    if GPIO.input(17) == 0:
        ret = True

    return ret

