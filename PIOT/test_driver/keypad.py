import paho.mqtt.client as mqtt

MATRIX = [
    [1,2,3],
    [4,5,6],
    [7,8,9],
    ['*',0,'#']
]

global cbk_func
client = None

def on_connect(client, userdata, flags, rc):
    print("Keypad MQTT connected, rc =", rc)
    client.subscribe("test/keypad") 

def on_message(client, userdata, msg):
    global cbk_func
    key = msg.payload.decode().strip()
    if key.isdigit():
        key = int(key)
    if cbk_func:
        cbk_func(key)

def init(key_press_cbk):

    global cbk_func, client
    cbk_func = key_press_cbk

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set("user","pokemongo")
    client.connect("140.245.45.204", 1883, 60)
    client.loop_start()

def get_key():
 
    pass