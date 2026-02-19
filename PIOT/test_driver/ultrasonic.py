


import paho.mqtt.client as mqtt

distance  = 999


def on_connect(client, userdata, flags, rc):
    client.subscribe("test/ultrasonic") 

def on_message(client, userdata, msg):
    global distance
    distance = int(msg.payload.decode())

def init():

    global client,distance
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set("user","pokemongo")
    client.connect("140.245.45.204", 1883, 60)
    client.publish("test/ultrasonic", distance, retain=True)
    client.loop_start()
    

def get_distance():

    return distance
