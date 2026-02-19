import time
import datetime
import threading
import csv
import psycopg2
import paho.mqtt.client as mqtt
import os
import configparser
from flask import Flask, render_template, request, redirect, session,url_for,send_file, abort
import psycopg2
IMAGE_FOLDER = "static/image"
os.makedirs(IMAGE_FOLDER, exist_ok=True)
ip = None
port = None
mqttuser = None
mqttpassword = None
data_store = {}


client = mqtt.Client()
def load_mqttconfig():
    global ip,port,mqttuser,mqttpassword
    config = configparser.ConfigParser()
    config.read('config.ini')
    ip = config.get('MQTT', 'IP')
    port = config.get('MQTT', 'PORT')
    mqttuser = config.get('MQTT', 'USER')
    mqttpassword = config.get('MQTT', 'PASSWORD')

        
def on_connect(client, userdata, flags, rc):
    print("Connected:", rc)
    client.subscribe("+/#") 


def on_message(client, userdata, msg):
    topic = msg.topic  
    parts = topic.split("/")    
    house = parts[0]

    if house not in data_store:
        data_store[house] = {}

    try:
        if len(parts) == 3:
            key = f"{parts[1]}_{parts[2]}"
        elif len(parts) == 2:
            key = parts[1]
        else:
            key = parts[-1]

        if key == "camera":
            image_path = os.path.join(IMAGE_FOLDER, f"{house}_camera.jpg")
            with open(image_path, "wb") as f:
                f.write(msg.payload)
            data_store[house]["camera_image"] = image_path


        else:

            try:
                payload = msg.payload.decode("utf-8")
            except UnicodeDecodeError:

                payload = msg.payload


            try:
                value = float(payload)
            except (ValueError, TypeError):
                value = payload  #

            data_store[house][key] = value



    except Exception as e:
        print("Error processing message:", e)

load_mqttconfig()
client.username_pw_set(mqttuser,mqttpassword)
client.on_connect = on_connect
client.on_message = on_message
client.connect(ip,int(port),60)
client.loop_start() 

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

def load_logs():
    try:
        items = []
        conn = connect_db()
        cur = conn.cursor()
        
     
        cur.execute("""SELECT * FROM logs
        WHERE house = %s
        ORDER BY date_time DESC;""", (mqttuser,))
        rows = cur.fetchall()
        for i in rows:
            items.append({"message":i[2],"datetime":i[3]})
        cur.close()
        conn.close()
        return (items)
    except:
        return ("error")
def load_user():
    items = []
    conn = connect_db()
    cur = conn.cursor()
    
    print("\nFetching item in PostgresSQL DB...")
    cur.execute("SELECT * FROM home;")
    rows = cur.fetchall()
    for i in rows:
        items.append({"id":i[0],"house":i[1],"online_user":i[2],"online_password":i[3]})
    cur.close()
    conn.close()
    print (items)
    return (items)
# WEBSIE CODE
app = Flask(__name__)
app.secret_key = 'piot_smart_home'


@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/login', methods=['GET','POST'])
def login():
   
   if request.method == 'POST':
  
       name = request.form['name']
       passinput = request.form['pass']
       user = load_user()
       for u in user:
           if u['online_user'] == name and u['online_password'] == passinput:

                       session['username'] = u['online_user']
                       session['house'] = u['house']
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
       return render_template('index.html',user = session['username'], house = session['house'])
            
@app.route('/log')
def log():
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
       logs = load_logs()
       return render_template('log.html', logs = logs)
            

            
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
    
    
#API endpoint
@app.route('/toggle_light')
def togglelight():
    global light
    if 'house' not in session:
        return redirect(url_for('login'))
    else: 
        house = session['house']
        light_state = data_store.get(house, {}).get("light_state", "False")
        if light_state == "True":
            client.publish(f"{house}/light/command", "0")
        else:
            client.publish(f"{house}/light/command", "1")
        return redirect(url_for('home'))

@app.route('/autolight')
def autolight():
    global autolight
    if 'house' not in session:
        return redirect(url_for('login'))
    else: 
        house = session['house']
        autolight = data_store.get(house, {}).get("light_auto", "Manual")
        if autolight == "Manual":
            client.publish(f"{house}/light/auto/command", "1")
        else:
            client.publish(f"{house}/light/auto/command", "0")
        return redirect(url_for('home'))
    
@app.route('/toggle_window')
def windowswitch():
    global window, prevwindow
    if 'house' not in session:
        return redirect(url_for('login'))
    else:
        house = session['house']
        window_state = data_store.get(house, {}).get("window", "False")
        if window_state == "True":
            client.publish(f"{house}/window/command", "0")
        else:
            client.publish(f"{house}/window/command", "1")
        return redirect(url_for('home'))
    
@app.route('/autowindow')
def autowindow():
    global autowindow
    if 'house' not in session:
        return redirect(url_for('login'))
    else: 
            house = session['house']
            autowindow = data_store.get(house, {}).get("window_auto", "Manual")
            if autowindow == "Manual":
                client.publish(f"{house}/window/auto/command", "1")
            else:
                client.publish(f"{house}/window/auto/command", "0")
            return redirect(url_for('home'))
        
@app.route('/takephoto')
def takephoto():
    if 'house' not in session:
        return redirect(url_for('login'))
    else: 
        house = session['house']
        client.publish(f"{house}/camera/command", "1")
        return redirect(url_for('home'))
        
        
@app.route('/resetalarm')
def reset():
    if 'house' not in session:
        return redirect(url_for('login'))
    else: 
        house = session['house']
        client.publish(f"{house}/resetalarm", "1")
        return redirect(url_for('home'))
# data endpoint

@app.route('/mode')
def getmode():
    if 'house' not in session:
        return redirect(url_for('login'))

    house = session['house']
    mode = data_store.get(house, {}).get("mode", "")
    return str(mode)


@app.route('/status')
def getstatus():
    if 'house' not in session:
        return redirect(url_for('login'))

    house = session['house']
    status = data_store.get(house, {}).get("status", "")
    return str(status)


@app.route('/temp')
def gettemp():
    if 'house' not in session:
        return redirect(url_for('login'))

    house = session['house']
    temp = data_store.get(house, {}).get("dht_temp", "")
    return str(temp)


@app.route('/humidity')
def gethumidity():
    if 'house' not in session:
        return redirect(url_for('login'))

    house = session['house']
    humidity = data_store.get(house, {}).get("dht_humidity", "")
    return str(humidity)


@app.route('/window')
def getwindow():
    if 'house' not in session:
        return redirect(url_for('login'))

    house = session['house']
    window_state = data_store.get(house, {}).get("window", "False")
    # Convert string "True"/"False" to readable
    return "Close" if window_state == "True" else "Open"


@app.route('/lock')
def getlock():
    if 'house' not in session:
        return redirect(url_for('login'))

    house = session['house']
    lock_state = data_store.get(house, {}).get("door_lock_lock", "False")
    return "Lock" if lock_state == "True" else "Unlock"


@app.route('/lightmode')
def getlightmode():
    if 'house' not in session:
        return redirect(url_for('login'))

    house = session['house']
    autolight = data_store.get(house, {}).get("light_auto", "Manual")
    return str(autolight)


@app.route('/light')
def getlight():
    if 'house' not in session:
        return redirect(url_for('login'))

    house = session['house']
    light_state = data_store.get(house, {}).get("light_state", "False")
    autolight = data_store.get(house, {}).get("light_auto", "Auto")

    if autolight != "Auto":
        return "On" if light_state == "True" else "Off"
    else:
        return " "


@app.route('/lastaccess')
def getlastaccess():
    if 'house' not in session:
        return redirect(url_for('login'))

    house = session['house']
    last_access = data_store.get(house, {}).get("door_lock_last_access", "")
    return str(last_access)


@app.route('/windowmode')
def getwindowmode():
    if 'house' not in session:
        return redirect(url_for('login'))

    house = session['house']
    autowindow = data_store.get(house, {}).get("window_auto", "Manual")
    return str(autowindow)


@app.route('/rain')
def getrain():
    if 'house' not in session:
        return redirect(url_for('login'))

    house = session['house']
    rain = data_store.get(house, {}).get("rain", "No")
    return str(rain)
@app.route("/camera")
def get_camera():
 
    if 'username' not in session:
        return "Not logged in", 401

    house = session['house']

 
    image_path = data_store.get(house, {}).get("camera_image")

    if image_path and os.path.exists(image_path):

        return send_file(image_path, mimetype='image/jpeg')
    else:

        abort(404)
if __name__ == "__main__":
  

    app.run(host="0.0.0.0", port = 5000)