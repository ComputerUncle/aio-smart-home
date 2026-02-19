import requests
import time
import threading
import psycopg2
import configparser
import paho.mqtt.client as mqtt
# Add at the top before your Telegram functions
import os

# Store live device states
data_store = {}

# MQTT setup
client = mqtt.Client()

# Load MQTT config from config.ini
config = configparser.ConfigParser()
config.read('config.ini')
ip = config.get('MQTT', 'IP')
port = int(config.get('MQTT', 'PORT'))
mqttuser = config.get('MQTT', 'USER')
mqttpassword = config.get('MQTT', 'PASSWORD')

client.username_pw_set(mqttuser, mqttpassword)

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT with code", rc)
    client.subscribe("+/#")  
def on_message(client, userdata, msg):

    topic = msg.topic.strip("/")
    parts = topic.split("/")


    if len(parts) < 1:
        return

    house = parts[0]

    if house not in data_store:
        data_store[house] = {}


    if "camera" in parts:
        image_path = os.path.join("static/image", f"{house}_camera.jpg")
        os.makedirs("static/image", exist_ok=True)  # ensure folder exists
        with open(image_path, "wb") as f:
            f.write(msg.payload)

        data_store[house]["camera_image"] = image_path
        print(f"Saved camera image for {house} -> {image_path}")
        return


    try:
        key = "_".join(parts[1:]) if len(parts) > 1 else parts[-1]

        # Try decode payload
        try:
            payload = msg.payload.decode("utf-8")
        except:
            payload = msg.payload


        try:
            value = float(payload)
        except (ValueError, TypeError):
            value = payload

        data_store[house][key] = value
        print(f"[MQTT] {house}/{key} -> {value}")


        if key == "event":
            for chat_id, user_house in telegram_users.items():
                if user_house == house:
                    send_message(chat_id, f"{value}")


        if key == "event_image":

            try:
                trigger = int(float(value))
            except:
                trigger = 0

            if trigger == 1:
               

                for chat_id, user_house in telegram_users.items():
                    if user_house == house:
                        send_message(chat_id, "Type /getphoto to see the camera image.")


    except Exception as e:
        print("Error processing MQTT message:", e)


client.on_connect = on_connect
client.on_message = on_message
client.connect(ip, port, 60)
client.loop_start()


TOKEN = "8457382480:AAGzq46WuwVnKuhCDZ4YOjX8CNB6kr5WBSc"
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"


telegram_users = {}

def get_updates(offset=None):
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    response = requests.get(url, params=params)
    return response.json()

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)


def load_db_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    host = config.get('Database', 'host')
    port = config.get('Database', 'port')
    database = config.get('Database', 'database')
    connect_timeout = config.get('Database', 'connect_timeout')
    return {'host': host, 'port': port, 'database': database, 'connect_timeout': int(connect_timeout)}

def load_db_credential():
    config = configparser.ConfigParser()
    config.read('credential.ini')
    user = config.get('credential', 'user')
    password = config.get('credential', 'password')
    return {'user': user, 'password': password}

def connect_db():
    db = load_db_config()
    dbc = load_db_credential()
    return psycopg2.connect(
        host=db['host'],
        port=db['port'],
        user=dbc['user'],
        password=dbc['password'],
        database=db['database'],
        connect_timeout=db['connect_timeout']
    )

def verify_user(username, password):
    """Check if user exists in Postgres and return house"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT house FROM home WHERE online_user=%s AND online_password=%s", (username, password))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0]  # house_name
    return None

def handle_start(chat_id):
    message = (
        "Welcome to Smart Home Bot!\n"
        "Commands:\n"
        "/login <username> <password> - Login with your credentials\n"
        "/status - Check your login status\n"
        "/help - Show this menu\n"
        "/toggle_light - Toggle light\n"
        "/toggle_window - Toggle window\n"
        "/takephoto - Take a camera photo"
        "/getphoto - To get latest photo"
    )
    send_message(chat_id, message)

def handle_login(chat_id, text):
    parts = text.split()
    if len(parts) != 3:
        send_message(chat_id, "Usage: /login <username> <password>")
        return
    username, password = parts[1], parts[2]
    house = verify_user(username, password)
    if house:
        telegram_users[chat_id] = house
        send_message(chat_id, f"Login successful! Your house: {house}")
    else:
        send_message(chat_id, "Login failed. Check your username and password.")

def handle_status(chat_id):
    house = telegram_users.get(chat_id)
    if house:
        send_message(chat_id, f"Logged in with house: {house}")
    else:
        send_message(chat_id, "You are not logged in. Use /login <username> <password>.")
def handle_getphoto(chat_id):
    house = telegram_users.get(chat_id)
    if not house:
        send_message(chat_id, "You need to login first.")
        return

    image_path = data_store.get(house, {}).get("camera_image")
    if image_path and os.path.exists(image_path):
        url = f"{TELEGRAM_API}/sendPhoto"
        with open(image_path, "rb") as img:
            files = {"photo": img}
            data = {"chat_id": chat_id}
            requests.post(url, files=files, data=data)
    else:
        send_message(chat_id, "No photo available yet. Take one first with /takephoto.")
def handle_device_command(chat_id, text):

    house = telegram_users.get(chat_id)
    if not house:
        send_message(chat_id, "You need to login first. Use /login <username> <password>")
        return

    if text == "/toggle_light":
        light_state = data_store.get(house, {}).get("light_state", "False")
        new_state = "0" if light_state=="True" else "1"
        client.publish(f"{house}/light/command", new_state)
        send_message(chat_id, f"Light toggled to {new_state}")
    elif text == "/toggle_window":
        window_state = data_store.get(house, {}).get("window", "False")
        new_state = "0" if window_state=="True" else "1"
        client.publish(f"{house}/window/command", new_state)
        send_message(chat_id, f"Window toggled to {new_state}")
    elif text == "/takephoto":
        client.publish(f"{house}/camera/command", "1")
        send_message(chat_id, "Camera triggered! Wait a moment and then send /getphoto to retrieve the image.")

def send_alert_to_house(house, message):
    for chat_id, user_data in users.items():
        if user_data.get("house") == house:
            send_message(chat_id, f"[{house}] {message}")


def telegram_loop():
    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates.get("result", []):
            offset = update["update_id"] + 1
            if "message" in update:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"].get("text", "")
                print(f"Telegram message from {chat_id}: {text}")

                if text.startswith("/start") or text.startswith("/help"):
                    handle_start(chat_id)
                elif text.startswith("/login"):
                    handle_login(chat_id, text)
                elif text.startswith("/status"):
                    handle_status(chat_id)
                elif text.startswith("/toggle_light") or text.startswith("/toggle_window") or text.startswith("/takephoto"):
                    handle_device_command(chat_id, text)
                elif text.startswith("/getphoto"):
                    handle_getphoto(chat_id)
                else:
                    send_message(chat_id, "Unknown command. Type /help for commands.")
        time.sleep(1)


telegram_loop()