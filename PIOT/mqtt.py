import time
import paho.mqtt.client as mqtt
from driver import gettemphumid as dht

IP = "140.245.45.204"
PORT = 1883
USER = "user"
PASSWORD = "pokemongo"

client = mqtt.Client()
client.username_pw_set(USER,PASSWORD)
client.connect(IP,PORT,60)

dht.init()

def main():
    print("Starting")
    while True:
        time.sleep(2)
        temp,humidity,error = dht.read_temp_humidity()
        client.publish("dht/temp", temp)
        client.publish("dht/humidity", humidity)
        client.publish("dht/error", error)
        
if __name__ == "__main__":
    main()