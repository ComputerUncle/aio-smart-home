import RPi.GPIO as GPIO #import RPi.GPIO module
from time import sleep


GPIO.setmode(GPIO.BCM) #choose BCM mode
GPIO.setwarnings(False)
GPIO.setup(26,GPIO.OUT) #set GPIO 26 as output
PWM=GPIO.PWM(26,50) #set 50Hz PWM output at GPIO26


def open():
    PWM.start(7.5) 
    #print('door opening')
    
def close():
    PWM.start(5) 
    #print('door closing')
