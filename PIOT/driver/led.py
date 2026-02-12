import RPi.GPIO as GPIO

PWM = None
def init():
    global PWM
    GPIO.setmode(GPIO.BCM)  # choose BCM mode
    GPIO.setwarnings(False)
    GPIO.setup(24, GPIO.OUT)  # set GPIO 24 as output
    PWM = GPIO.PWM(24, 1000)
    PWM.start(0)

def set_output(level):
    global PWM
    if level == True:
        PWM.ChangeDutyCycle(0)
    else:
        PWM.ChangeDutyCycle(100)
    
    
def setbrightness(brightness):
    global PWM
    if brightness >=0 and brightness <=100:
        PWM.ChangeDutyCycle(brightness)
    
    
