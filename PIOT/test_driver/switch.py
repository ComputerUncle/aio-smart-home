import paho.mqtt.client as mqtt

slide_state = 0 


def on_connect(client, userdata, flags, rc):
    client.subscribe("test/slide_switch") 

def on_message(client, userdata, msg):
    global slide_state
    payload = msg.payload.decode().strip()
    if payload in ("1", "True"):
        slide_state = 1
    else:
        slide_state = 0

def init():

    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set("user","pokemongo")
    client.connect("140.245.45.204", 1883, 60)
    client.publish("test/slide_switch",slide_state, retain=True)
    client.loop_start()

def read_slide_switch():

    return slide_state
