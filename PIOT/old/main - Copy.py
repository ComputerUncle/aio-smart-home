import time
import datetime
import threading
import paho.mqtt.client as mqtt
from driver import gettemphumid as dht
from driver import lcd as LCD
from driver import keypad
from driver import ultrasonic
from driver import rfid
from driver import door
from driver import adc
from driver import led
from driver import switch
from driver import ir
from driver import moisture
from driver import motor
from driver import accelerometer
import configparser
from flask import Flask, render_template, request, redirect, session,url_for
#timer
starttime = time.time()
keypadt = None
ct = time.time()
#Variable
temp = None
humidity = None
error = None
ip = None
port = None
user = None
password = None
usdistance = None
correctpin = [2]
pininput = []
cont_incorrect = 0
prevlock = True
prevwindow = None
prevlight = None
#State
mode = 0
lockcooldown = 0
locktimer = 0
autolight = False
autowindow = False
lockdown = False
fire = False
#
#String

door_lock = True
window = True
windowtimer = None
doorlocktimer = None
client = mqtt.Client()
def load_mqttconfig():
    global ip,port,user,password
    config = configparser.ConfigParser()
    config.read('config.ini')
    ip = config.get('MQTT', 'IP')
    port = config.get('MQTT', 'PORT')
    user = config.get('MQTT', 'USER')
    password = config.get('MQTT', 'PASSWORD')

load_mqttconfig()
client.username_pw_set(user,password)
client.connect(ip,int(port),60)
lcd= LCD.lcd()
dht.init()
reader = rfid.init()
adc.init()
led.init()
switch.init()
ir.init()
moisture.init()
motor.init()
accelerometer.init
def map( x,in_min, in_max, out_min, out_max):
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def key_pressed(key):
    global pininput,correctpin,cont_incorrect,lockcooldown,door_lock,mode
    if lockcooldown == 0:
        if key == "#":
            if pininput == correctpin:
                 lcd.lcd_clear()
                 lcd.lcd_display_string("Correct Pin",1)
                 lcd.lcd_display_string(" ",2)
                 door_lock = False
                 pininput = []
            else:
                lcd.lcd_clear()
                lcd.lcd_display_string("Wrong Pin",1)
                lcd.lcd_display_string(" ",2)
                pininput = []
                cont_incorrect = cont_incorrect + 1
                if cont_incorrect >3:
                    lockcooldown = 5
                    cont_incorrect =0
        elif key == "*":
            lcd.lcd_clear()

            pininput = []
        else:
            pininput.append(key)
            lcd.lcd_display_string(str(key),2,len(pininput)-1)
        
def mqttupdate():
    global temp,humidity,error,user,door_lock
  
        #DHT11
    client.publish(f"{user}/dht/temp", temp)
    client.publish(f"{user}/dht/humidity", humidity)
    client.publish(f"{user}/dht/error", error)
        #Mode
    client.publish(f"{user}/mode", mode)
        #Light
    client.publish(f"{user}/light/auto", autolight, retain = True)
        #Window
    client.publish(f"{user}/window", window, retain = True)
        #Moisture
        #Lock
    client.publish(f"{user}/door_lock/lock", door_lock , retain= True)
def dht11(interval):
    global temp,humidity,error
    temp,humidity,error = dht.read_temp_humidity()
    client.publish(f"{user}/dht/temp", temp)
    client.publish(f"{user}/dht/humidity", humidity)
    client.publish(f"{user}/dht/error", error)
def ultrasonic():
    global usdistance
    usdistance = ultrasonic.getdistance()
def doorlock():
    global lockcooldown,locktimer,prevlock,door_lock,doorlocktimer,ct
    if lockcooldown >0:
            
           
            if locktimer == None:
                locktimer = ct
            
            if time.time() - locktimer > 1:
                lockcooldown = lockcooldown -1
                lcd.lcd_clear()
                lcd.lcd_display_string("Too many attempt",1)
                lcd.lcd_display_string(f"Wait for {lockcooldown}s",2)
                locktimer = ct
                if lockcooldown == 0:
                    lcd.lcd_clear()
    else:
        if locktimer == None:
                locktimer = ct
        if door_lock != prevlock:
            if door_lock == False:
                print ("Unlocked")
                client.publish(f"{user}/door_lock/lock", door_lock , retain= True)
                now = datetime.datetime.now()
                client.publish(f"{user}/door_lock/last_access", str(now.strftime("%c")),qos =1,retain = True)
                door.open()
                doorlocktimer = ct
                prevlock = door_lock
        if doorlocktimer != None:
            if time.time() - doorlocktimer > 3:
                door_lock = True
                print("Locked")
                door.close()
                client.publish(f"{user}/door_lock/lock", door_lock , retain= True)
                doorlocktimer = None
                prevlock = door_lock
                

                
def potentiomode():
    global mode
    value = adc.get_adc_value(1)
    #print (value)
    if value >= 0 and value <=341:
        mode = 0
    elif value > 341 and value <=682:
        mode = 1
    elif value > 682 and value <= 1023:
        mode = 2

def rfidsystem(interval):
        global lockcooldown,cont_incorrect,door_lock
    #while True:
        time.sleep(interval)
        if lockcooldown ==0:
            val = reader.read_id_no_block()
            if val != None:
                if val == 287063233418 or val == 470302458585:
                    lcd.lcd_clear()
                    lcd.lcd_display_string("Access granted",1)
                    lcd.lcd_display_string(" ",2)
                    door_lock = False
                else:
                     lcd.lcd_clear()
                     lcd.lcd_display_string("Invalid card",1)
                     lcd.lcd_display_string(" ",2)
                     time.sleep(2)
                     cont_incorrect = cont_incorrect + 1
                     if cont_incorrect >3:
                        lockcooldown = 30
                        
def intrudersys():
    global mode,lockdown
    if mode ==2:
        value = ir.get_ir_sensor_state()
        if value == True:
            if lockdown == False:
                print("WARNING")
                lockdown = True
def rainsystem():
    if autowindow == True:
        value = moisture.read_sensor()
        if value == True:
            window = True
def lightsystem():
    global prevlight
    if (switch.read_slide_switch() != prevlight):
            if (switch.read_slide_switch() == 1):
                client.publish(f"{user}/light/state", True, retain = True)
                led.set_output(True)
            else:
                led.set_output(False)
                client.publish(f"{user}/light/state", False, retain = True)
                
            prevlight = switch.read_slide_switch()
    if autolight == True:
  
        ldr = adc.get_adc_value(0)
        value = 1023 - ldr
        led.setbrightness(map(value,600,1023,0,100))
def key(hz):
    global keypadt,ct
    period = 1/hz
    if keypadt ==None:
        keypadt = ct
    
    #while True:

    if ct - keypadt > period:
            keypad.get_key()
            keypadt = time.time()
            
def windowf():
    global window, windowtime,prevwindow
    if window != prevwindow:
        if window == True:
            motor.set_motor_speed(100)
        else:
            motor.set_motor_speed(100)
        windowtime = time.time()
        client.publish(f"{user}/window", window, retain = True)
        prevwindow = window
        
    if windowtime != None:
        if time.time()-windowtime >=2:
            motor.set_motor_speed(0)
            windowtime = None
def firesystem():
    global temp,fire
    if temp != None:
        if temp >10:
            if fire == False:
                print ("FIRE!")
                fire = True
def main():
    global lockcooldown,ct
    keypad.init(key_pressed)
    

    print("Starting")
    prevtime = -9
    prevdebugtime = -9
    tcycle = 0
    performancedebug = False
    while True:
        ct = time.time()
        key(150)
        uptime = round(ct,2) - round(starttime,2)
        
        if uptime != prevtime:
            if (uptime % 0.01):
                lightsystem()
                intrudersys()
                windowf()
                firesystem()
            #prevtime = uptime
            if (uptime % 1 == 0):
                rfidsystem(0)
                potentiomode()
                lightsystem()
                rainsystem()
            if (uptime % 2 == 0):
                dht11(0)
                mqttupdate()
    
            prevtime = uptime
        doorlock()
        
        
        
        #To test for performance
        if performancedebug == True:
            if uptime != prevdebugtime:
                if (uptime % 2 == 0):
                    if uptime != 0:
                        CPS = tcycle / uptime
                        print(f"CPS [Clock per second] = {CPS}Hz, Total clock is {tcycle}")

        prevdebugtime = uptime
        
        
        
        
        tcycle = tcycle + 1



# WEBSIE CODE
app = Flask(__name__)
app.secret_key = 'piot_smart_home'




@app.route('/login', methods=['GET','POST'])
def login():
   global user,password
   if request.method == 'POST':
       name = request.form['name']
       passinput = request.form['pass']
       
       if name == user and passinput == password:
                   session['username'] = user
                   return redirect(url_for('home'))
       else: 
                   return render_template('login.html', status = "Wrong Password")
          
   if 'username' not in session:
       return render_template('login.html')
   else: 
       return redirect(url_for('home'))

            
@app.route('/window')
def windowswitch():
    global window
    window = not window
    return redirect(url_for('login'))

            

            
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))




if __name__ == "__main__":
    mainthread = threading.Thread(target=main)
    mainthread.start()

    app.run(host="0.0.0.0", port = 5000)