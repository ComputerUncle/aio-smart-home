import paho.mqtt.client as mqtt

SENSOR_TOPIC = "test/moisture"
sensor_value = False   

client = mqtt.Client()
client.username_pw_set("user","pokemongo")
client.connect("140.245.45.204", 1883, 60)
client.loop_start()

def on_message(client, userdata, msg):
    global sensor_value
    payload = msg.payload.decode().strip().lower()
    if payload in ["1", "true", "on"]:
        sensor_value = True
    else:
        sensor_value = False

client.on_message = on_message
client.subscribe(SENSOR_TOPIC)

def init():
    global sensor_value
    sensor_value = False 

def read_sensor():
    global sensor_value
    return sensor_value
