import time

import RPi.GPIO as GPIO

from . import dht11

prev_valid_ret = [0,0,0]
cont_error =0
def init():
    GPIO.setmode(GPIO.BCM)
    global dht11_inst

    dht11_inst = dht11.DHT11(pin=21)  # read data using pin 21

def read_temp_humidity():

    global dht11_inst,prev_valid_ret,cont_error
    ret = [-100, -100,0]
    result = dht11_inst.read()

    if result.is_valid():
        #print("Temperature: %-3.1f C" % result.temperature)
        #print("Humidity: %-3.1f %%" % result.humidity)

        ret[0] = result.temperature
        ret[1] = result.humidity
        prev_valid_ret = ret
        cont_error = 0
        ret[2] = cont_error

    else:
        if prev_valid_ret == [0,0,0]:
            error = 0
            while not result.is_valid():
                time.sleep(1)
                result = dht11_inst.read()
                error = error +1
                if error >5:
                    print("DHT11 unable to get reading, please check sensor")
            prev_valid_ret[0] = result.temperature
            prev_valid_ret[1] = result.humidity
            prev_valid_ret[2] = 1
        ret = prev_valid_ret
        cont_error = cont_error + 1
        ret[2] = cont_error
        #print (f"error {cont_error}x")
       
    if cont_error >5:
        print("DHT11 detected more than 5 continuous error, please check sensor and main code")
    return ret


