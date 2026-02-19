import paho.mqtt.client as mqtt
import time

class MQTTMFRC522:

    
    def __init__(self):
        self.last_id = None

        # Setup MQTT client
        self.client = mqtt.Client()
        self.client.on_message = self._on_message
        self.client.username_pw_set("user","pokemongo")
        self.client.connect("140.245.45.204", 1883, 60)
        self.client.subscribe("test/rfid")
        self.client.loop_start()

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        if payload != "" and payload.lower() != "none":
            self.last_id = payload 

    def read_id(self):
 
        while self.last_id is None:
            time.sleep(0.1)
        val = self.last_id
        self.last_id = None  
        return int(val)

    def read_id_no_block(self):

        if self.last_id is not None:
            val = self.last_id
            self.last_id = None
            return int(val)
        return None


def init():

    rfid_reader = MQTTMFRC522()
    return rfid_reader
