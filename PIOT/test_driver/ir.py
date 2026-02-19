import paho.mqtt.client as mqtt

ir_state = False  

def on_connect(client, userdata, flags, rc):
    client.subscribe("test/ir")  

def on_message(client, userdata, msg):
    global ir_state
    payload = msg.payload.decode()
    if payload in ("0", "False"):
        ir_state = True 
    else:
        ir_state = False

def init():
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set("user","pokemongo")
    client.connect("140.245.45.204", 1883, 60)
    client.loop_start()

def get_ir_sensor_state():
    return ir_state
