import time
import datetime
import threading
import csv
import psycopg2
import paho.mqtt.client as mqtt
testing = True  #This testing does not use hardware driver but will mock hardware driver through the MQTT under "/test"
if testing:
    from test_driver import gettemphumid as dht
    from test_driver import lcd as LCD
    from test_driver import keypad
    from test_driver import ultrasonic
    from test_driver import rfid
    from test_driver import door
    from test_driver import adc
    from test_driver import led
    from test_driver import switch
    from test_driver import ir
    from test_driver import moisture
    from test_driver import motor
    from test_driver import accelerometer
    from test_driver import buzzer
    from test_driver import cam
    
else:   
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
    from driver import buzzer
import configparser
from flask import Flask, render_template, request, redirect, session,url_for
#timer
starttime = time.time()
keypadt = None
ct = time.time()
#Variable
rfidval = None
temp = None
humidity = None
error = None
ip = None
port = None
mqttuser = None
mqttpassword = None
user = None
password = None
usdistance = None
correctpin = [2]
pininput = []
rfidlist = None
cont_incorrect = 0
prevlock = True
prevwindow = None
prevlight = None
prevalarm = None
alarm = False
cont_vib = 0
status = "Normal"
bell = False
belltimer = None
#State
mode = 0
lockcooldown = 0
locktimer = 0
autolight = True
autowindow = True
lockdown = False
fire = False
light= False
#
#String
last_access = None
door_lock = True
window = True
windowtimer = None
doorlocktimer = None
client = mqtt.Client()
def load_mqttconfig():
    global ip,port,mqttuser,mqttpassword
    config = configparser.ConfigParser()
    config.read('config.ini')
    ip = config.get('MQTT', 'IP')
    port = config.get('MQTT', 'PORT')
    mqttuser = config.get('MQTT', 'USER')
    mqttpassword = config.get('MQTT', 'PASSWORD')
def load_auth():
    global user,password
    config = configparser.ConfigParser()
    config.read('config.ini')
    user = config.get('AUTH','user')
    password = config.get('AUTH','pass')
    if not user:
        user = config.get('KEY','name')
        password = config.get('KEY','pass')
load_auth()
load_mqttconfig()
client.username_pw_set(mqttuser,mqttpassword)
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
buzzer.init()
ultrasonic.init()
acc = accelerometer.init()
prev_x,prev_y,prev_z = acc.get_3_axis()

def load_db_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    

    host = config.get('Database', 'host')
    port = config.get('Database', 'port')
    database = config.get('Database', 'database')
    connect_timeout = config.get('Database', 'connect_timeout')
    
    config_values = {
        'host': host,
        'port': port,
        'database': database,
        'connect_timeout' : int(connect_timeout)
    }
    return config_values

def load_db_credential():
    config = configparser.ConfigParser()
    config.read('credential.ini')
    

    user = config.get('credential', 'user')
    password = config.get('credential', 'password')
    
    credential = {
        'user' : user,
        'password' : password
    }
    return credential
def connect_db():
    db = load_db_config()
    dbc = load_db_credential()
    return psycopg2.connect(
        host=db['host'],
        port=db['port'],
        user=dbc['user'],
        password=dbc['password'],
        database=db['database'],
        connect_timeout = db['connect_timeout']
        )
        
def log(message):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""INSERT INTO logs (house,message,date_time)
        VALUES (%s,%s,NOW());""",(mqttuser,message,))
        conn.commit()
        cur.close()
        conn.close()  
    except Exception as e:
        print(e)
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
                 log("Door unlocked through keypad")
                 door_lock = False
                 pininput = []
            else:
                lcd.lcd_clear()
                lcd.lcd_display_string("Wrong Pin",1)
                lcd.lcd_display_string(" ",2)
                pininput = []
                cont_incorrect = cont_incorrect + 1
                if cont_incorrect >3:
                    lockcooldown = 30
                    log("3 failed unlock attempts detected through keypad")
                    cont_incorrect =0
        elif key == "*":
            lcd.lcd_clear()

            pininput = []
        else:
            pininput.append(key)
            lcd.lcd_display_string(str(key),2,len(pininput)-1)
        
def mqttupdate():
    global temp,humidity,error,mqttuser,door_lock,alarm,status,autolight
  
        #DHT11
    client.publish(f"{mqttuser}/dht/temp", temp)
    client.publish(f"{mqttuser}/dht/humidity", humidity)
    client.publish(f"{mqttuser}/dht/error", error)
        #Mode
    client.publish(f"{mqttuser}/mode", mode)
        #Light
    client.publish(f"{mqttuser}/light/auto", "Auto" if autolight else "Manual", retain = True)
        #Window
    client.publish(f"{mqttuser}/window", window, retain = True)
    client.publish(f"{mqttuser}/window/auto", "Auto" if autowindow else "Manual", retain = True)
        #Moisture
    client.publish(f"{mqttuser}/rain", "Yes" if moisture.read_sensor() else "No", retain = True)
        #Lock
    client.publish(f"{mqttuser}/door_lock/lock", door_lock , retain= True)
    client.publish(f"{mqttuser}/status", status)

def dht11(interval):
    global temp,humidity,error
    temp,humidity,error = dht.read_temp_humidity()
    client.publish(f"{mqttuser}/dht/temp", temp)
    client.publish(f"{mqttuser}/dht/humidity", humidity)
    client.publish(f"{mqttuser}/dht/error", error)
def load_user():

    user = []

    try:
        with open('user.csv', 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                user.append({
                    'name': row['name'],
                    'rfid': int(row['rfid'])
                })
    except FileNotFoundError:
        print("Error: workouts.csv file not found!")
    except Exception as e:
        print(f"Error loading CSV: {e}")

    return user
    
def add_user(name, rfid):

    user = load_user()

    user.append({
        'name': name,
        'rfid': rfid
    })

    save_user(user)
    print("User added.")
    
    
def edit_user(name, new_name=None, new_rfid=None):

    user = load_user()

    for u in user:
        if u['name'] == name:
            if new_name:
                u['name'] = new_name
            if new_rfid:
                u['rfid'] = new_rfid

    save_user(user)
    print("User updated.")

def delete_user(name):

    user = load_user()

    user = [u for u in user if u['name'] != name]

    save_user(user)
    print("User deleted.")



def save_user(user):

    try:
        with open('user.csv', 'w', newline='') as file:
            fieldnames = ['name', 'rfid']
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(user)

    except Exception as e:
        print(f"Error saving CSV: {e}")
def send_image_mqtt():
    with open("static/image/image.jpg", "rb") as f:
        image_bytes = f.read()
    client.publish(f"{mqttuser}/camera", image_bytes,retain = True)

def doorlock():
    global lockcooldown,locktimer,prevlock,door_lock,doorlocktimer,ct,last_access
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
                client.publish(f"{mqttuser}/door_lock/lock", door_lock , retain= True)
                now = datetime.datetime.now()
                last_access = str(now.strftime("%c"))
                client.publish(f"{mqttuser}/door_lock/last_access", last_access,qos =1,retain = True)
                door.open()
                doorlocktimer = ct
                prevlock = door_lock
        if doorlocktimer != None:
            if time.time() - doorlocktimer > 3:
                door_lock = True
                print("Locked")
                door.close()
                client.publish(f"{mqttuser}/door_lock/lock", door_lock , retain= True)
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
        global lockcooldown,cont_incorrect,door_lock,rfidval
    #while True:
        time.sleep(interval)
        if lockcooldown ==0:
            if rfidval == None:
                val = reader.read_id_no_block()
                if val != None:
                    rfidval = val
                    for i in rfidlist:
                        if val == i["rfid"]:
                            lcd.lcd_clear()
                            lcd.lcd_display_string("Access granted",1)
                            lcd.lcd_display_string(" ",2)
                            log(f"{i["name"]} unlocked door")
                            door_lock = False
                            cont_incorrect = 0
                        else:
                             lcd.lcd_clear()
                             lcd.lcd_display_string("Invalid card",1)
                             lcd.lcd_display_string(" ",2)
                             time.sleep(2)
                             cont_incorrect = cont_incorrect + 1
                             if cont_incorrect >3:
                                log("3 failed unlock attempts detected through keycard")
                                lockcooldown = 30
                    rfidval = None
                        
def intrudersys():
    global mode,lockdown
    if mode ==2:
        value = ir.get_ir_sensor_state()
        if value == True:
            if lockdown == False:
                print("WARNING")
                lockdown = True
def rainsystem():
    global window, autowindow
    if autowindow == True:
        value = moisture.read_sensor()
        if value == True:
            window = True
def lightsystem():
    global prevlight,light,autolight
    if (switch.read_slide_switch() != prevlight):
            if (switch.read_slide_switch() == 1):
                client.publish(f"{mqttuser}/light/state", True, retain = True)
                light = True
            else:
                light = False
                client.publish(f"{mqttuser}/light/state", False, retain = True)
                
            prevlight = switch.read_slide_switch()
    if autolight == True:
        
        ldr = adc.get_adc_value(0)
        value = 1023 - ldr

        led.setbrightness(map(value,600,1023,0,100))

            
def lightf():
    global light
    if autolight != True:
        if light == True:
                led.set_output(True)
        else:
                
                led.set_output(False)
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
    global window, windowtimer,prevwindow
    if window != prevwindow:
        motor.set_motor_speed(100)
        windowtimer = time.time()
        client.publish(f"{mqttuser}/window", window, retain = True)
        prevwindow = window
 
   
    if windowtimer != None:
        if time.time()-windowtimer >=1:
         
            motor.set_motor_speed(0)
            windowtimer = None
def firesystem():
    global temp,fire
    if temp != None:
        if temp >40:
            if fire == False:
                print ("FIRE!")
                fire = True
                
def alarmsys():
    global status,cont_vib,lockdown,window,lock,fire,prevalarm,alarm,status,light,autolight
    if alarm == False:
        if fire == True:
            alarm = True
            if alarm != prevalarm:
                status = "FIRE DETECTED!"
                log("Fire alarm activated")
                prevalarm = alarm
                lock = False
                buzzer.turn_on()
                cam.take()
        elif lockdown == True:
            alarm = True
            if alarm != prevalarm:
                window= True
                lock = True
                autolight = False
                light = True
                cam.take()
                buzzer.turn_on()
                status = "Intruder detected"
                log("Intruder detected, lockdown activated!")
                prevalarm = alarm
        elif cont_vib >= 5:
            alarm = True
            if alarm != prevalarm:
                buzzer.turn_on()
                status = "Abnormal structure movement detected"
                log("Abnormal structure movement detected")
                cam.take()
                prevalarm = alarm

def resetalarm():
    global status,cont_vib,lockdown,window,lock,fire,prevalarm,alarm,status,light,autolight
    alarm = False
    cont_vib = 0
    lock = True
    lockdown = False
    fire = False
    buzzer.turn_off()
    status = "Normal"
    log("Alarm reseted")
    prevalarm = alarm

def accelerosystem():
    global prev_x,prev_y,prev_z,acc,cont_vib
    x, y, z = acc.get_3_axis()
    THRESHOLD = 0.15
    dx = abs(x - prev_x)
    dy = abs(y - prev_y)
    dz = abs(z - prev_z)


    vibration_level = dx + dy + dz

    if vibration_level > THRESHOLD:
        cont_vib = cont_vib +1
        print("VIBRATION DETECTED", vibration_level,cont_vib)
    else:
        cont_vib = 0
    

    prev_x, prev_y, prev_z = x, y, z
def doorbell():
    global bell, belltimer
    dist = ultrasonic.get_distance()
    if bell == False:
        if dist < 4:
            print ("Ding Dong!")
            bell = True
            buzzer.turn_on()
            belltimer = time.time()
    else:
        if belltimer != None:
            if time.time() - belltimer >= 1:
                buzzer.turn_off()
                bell = False
            
            
        
def main():
    global lockcooldown,ct,rfidlist
    keypad.init(key_pressed)
    

    print("Starting")
    rfidlist = load_user()
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
                lightf()
                intrudersys()
                windowf()
                firesystem()
                alarmsys()
             
            if (uptime % 1 == 0):
                rfidsystem(0)
                potentiomode()
                lightsystem()
                rainsystem()
                accelerosystem()
                doorbell()
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
@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
       return render_template('index.html')
            

            

            
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
    
    
#API endpoint
@app.route('/toggle_light')
def togglelight():
    global light
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        light = not light
        return redirect(url_for('home'))

@app.route('/autolight')
def autolight():
    global autolight
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        autolight = not autolight
        return redirect(url_for('home'))
    
@app.route('/toggle_window')
def windowswitch():
    global window, prevwindow
    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        if autowindow == False:
            window = not window
        else:
            if moisture.read_sensor() != True:
                window = not window
        return redirect(url_for('home'))
    
@app.route('/autowindow')
def autowindow():
    global autowindow
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        autowindow = not autowindow
        return redirect(url_for('home'))
        
@app.route('/takephoto')
def takephoto():
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        cam.take()
        send_image_mqtt()
        return redirect(url_for('home'))
        
        
@app.route('/resetalarm')
def reset():
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        resetalarm()
        return redirect(url_for('home'))
# data endpoint
@app.route('/mode')
def getmode():
    global mode
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        return (str(mode))
@app.route('/status')
def getstatus():
    global status
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        return (str(status))
@app.route('/temp')
def gettemp():
    global temp
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        return (str(temp))
@app.route('/humidity')
def gethumidity():
    global humidity
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        return (str(humidity))
@app.route('/window')
def getwindow():
    global window
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        if window == True:
            v = "Close"
        else:
            v = "Open"
        return (v)
@app.route('/lock')
def getlock():
    global door_lock
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        if door_lock == True:
            v = "Lock"
        else:
            v = "Unlock"
        return (v)
@app.route('/lightmode')
def getlightmode():
    global autolight
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        if autolight == True:
            v = "Auto"
        else:
            v = "Manual"
        return (v)
@app.route('/light')
def getlight():
    global light,autolight
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        if autolight != True:
            if light == True:
                v = "On"
            else:
                v = "Off"
            return (v)
        else:
            return (" ")

@app.route('/lastaccess')
def getlastaccess():
    global last_access
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        return (str(last_access))
    
@app.route('/windowmode')
def getwindowmode():
    global autowindow
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        if autowindow == True:
            v = "Auto"
        else:
            v = "Manual"
        return (v)
    
@app.route('/rain')
def getrain():
     
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        if moisture.read_sensor() == True:
            v = "Yes"
        else:
            v = "No"
        return (v)

    
if __name__ == "__main__":
    mainthread = threading.Thread(target=main)
    mainthread.start()

    app.run(host="0.0.0.0", port = 5000)