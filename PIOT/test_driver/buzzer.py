import time
import paho.mqtt.client as mqtt

MQTT_TOPIC = "test/buzzer"  # topic for this buzzer

def on_connect(client, userdata, flags, rc):
    print("Buzzer MQTT connected, rc =", rc)

def init():
    """Initialize MQTT client for buzzer simulation"""
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.username_pw_set("user","pokemongo")
    client.connect("140.245.45.204", 1883, 60)
    client.loop_start()

    client.publish(MQTT_TOPIC, "off", retain=True)

def deinit():
    """Stop buzzer (publish off) and cleanup"""
    client.publish(MQTT_TOPIC, "turn_off", retain=True)
    client.loop_stop()
    client.disconnect()

def short_beep(beep_interval=0.1):
    """Simulate short beep pattern"""
    client.publish(MQTT_TOPIC, "short_beep", retain=True)
    time.sleep(beep_interval * 4)

def turn_on():
    client.publish(MQTT_TOPIC, "turn_on", retain=True)

def turn_off():
    client.publish(MQTT_TOPIC, "turn_off", retain=True)

def turn_on_with_timer(duration):
    client.publish(MQTT_TOPIC, "turn_on_with_timer", retain=True)
    time.sleep(duration)
    client.publish(MQTT_TOPIC, "turn_off", retain=True)

def beep(ontime, offtime, repeatnum):
    client.publish(MQTT_TOPIC, "beep", retain=True)
    total_time = (ontime + offtime) * repeatnum
    time.sleep(total_time)
