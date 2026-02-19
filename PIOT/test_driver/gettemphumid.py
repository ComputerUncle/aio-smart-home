import paho.mqtt.client as mqtt

temp = -100
humidity = -100
error = 0

def on_connect(client, userdata, flags, rc):
    client.subscribe("test/dht11/temp")
    client.subscribe("test/dht11/humidity")
    client.subscribe("test/dht11/error")

def on_message(client, userdata, msg):
    global temp, humidity, error

    if msg.topic == "test/dht11/temp":
        temp = float(msg.payload.decode())

    elif msg.topic == "test/dht11/humidity":
        humidity = float(msg.payload.decode())

    elif msg.topic == "test/dht11/error":
        error = int(msg.payload.decode())

def init():
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set("user","pokemongo")
    client.connect("140.245.45.204", 1883, 60)
    client.publish("test/dht11/temp", -100, retain=True)
    client.publish("test/dht11/humidity", -100, retain=True)
    client.publish("test/dht11/error", 0, retain=True)
    client.loop_start()

def read_temp_humidity():
    return [temp, humidity, error]
    
    
init()