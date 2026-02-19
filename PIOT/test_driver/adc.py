

import paho.mqtt.client as mqtt

ldr = 0
pot = 0

def on_connect(client, userdata, flags, rc):
    client.subscribe("test/potentiometer")
    client.subscribe("test/ldr")

def on_message(client, userdata, msg):
    global ldr,pot

    if msg.topic == "test/potentiometer":
        pot = int(msg.payload.decode())

    elif msg.topic == "test/ldr":
        ldr = int(msg.payload.decode())

def init():
    global client, ldr, pot
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set("user","pokemongo")
    client.connect("140.245.45.204", 1883, 60)
    client.publish("test/ldr", ldr, retain=True)
    client.publish("test/potentiometer", pot, retain=True)
    client.loop_start()

def get_adc_value(adcnum):
    if adcnum == 0:
        return ldr
    elif adcnum ==1:
        return pot
