import paho.mqtt.client as mqtt

MQTT_TOPIC = "test/door"

def init():
    global client
    client = mqtt.Client()
    client.username_pw_set("user","pokemongo")
    client.connect("140.245.45.204", 1883, 60)
    client.loop_start()

def open():
    global client
    client.publish(MQTT_TOPIC, "open", retain=True)

def close():
    global client
    client.publish(MQTT_TOPIC, "close", retain=True)
init()