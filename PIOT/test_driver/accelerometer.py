import time
import json
import paho.mqtt.client as mqtt

class ADXL345Sim:
    def __init__(self):
        """
        Simulated ADXL345 sensor publishing/receiving via MQTT
        """
        self.topic = "test/accelerometer"  # <-- updated fixed topic
        self.x = 0
        self.y = 0
        self.z = 0

        # Offsets/gains from calibration (can be updated via MQTT too)
        self.x_offset = 0
        self.y_offset = 0
        self.z_offset = 0
        self.x_gain = 1
        self.y_gain = 1
        self.z_gain = 1

        # Setup MQTT client
        self.client = mqtt.Client(userdata=self)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set("user","pokemongo")
        self.client.connect("140.245.45.204", 1883, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"ADXL345Sim connected to MQTT, rc={rc}")
        client.subscribe(f"{self.topic}/data")   # subscribe to updates
        client.subscribe(f"{self.topic}/calib")  # optional calib updates

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        if msg.topic == f"{self.topic}/data":
            # Expect JSON: {"x":0.12, "y":-0.03, "z":0.98}
            data = json.loads(payload)
            self.x = data.get("x", 0)
            self.y = data.get("y", 0)
            self.z = data.get("z", 0)
        elif msg.topic == f"{self.topic}/calib":
            # optional: JSON {"x_offset":..,"y_offset":..,"z_offset":..,"x_gain":..,"y_gain":..,"z_gain":..}
            data = json.loads(payload)
            self.x_offset = data.get("x_offset", self.x_offset)
            self.y_offset = data.get("y_offset", self.y_offset)
            self.z_offset = data.get("z_offset", self.z_offset)
            self.x_gain = data.get("x_gain", self.x_gain)
            self.y_gain = data.get("y_gain", self.y_gain)
            self.z_gain = data.get("z_gain", self.z_gain)

    # Simulate original functions
    def get_3_axis(self):
        return self.x, self.y, self.z

    def get_3_axis_adjusted(self):
        x_adj = (self.x - self.x_offset)/self.x_gain
        y_adj = (self.y - self.y_offset)/self.y_gain
        z_adj = (self.z - self.z_offset)/self.z_gain
        return x_adj, y_adj, z_adj

    def get_pitch(self):
        import math
        x_adj, y_adj, z_adj = self.get_3_axis_adjusted()
        return math.degrees(math.atan2(x_adj, math.hypot(y_adj, z_adj)))

    # Calibration save/load can be faked for simulation
    def calibrate(self):
        print("Simulated calibrate() called - use MQTT to update calib if needed")

    def save_calib_value(self):
        print("Simulated save_calib_value() called")

    def load_calib_value(self):
        print("Simulated load_calib_value() called")

    def measure_start(self):
        print("Simulated measure_start() called")

    def measure_stop(self):
        print("Simulated measure_stop() called")
def init():
    print("Running simulator init...")
    acc = ADXL345Sim()
    return acc