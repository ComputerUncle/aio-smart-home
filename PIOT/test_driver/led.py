import paho.mqtt.client as mqtt

PWM_TOPIC = "test/led"

PWM_value = 0 
client = mqtt.Client()
client.username_pw_set("user","pokemongo")
client.connect("140.245.45.204", 1883, 60)
client.loop_start()

def init():
    global PWM_value
    PWM_value = 0
    client.publish(PWM_TOPIC, PWM_value)

def set_output(level):
    """True=0, False=100 (like original GPIO)"""
    global PWM_value
    PWM_value = 100 if level else 0
    client.publish(PWM_TOPIC, PWM_value)

def setbrightness(brightness):
    """0-100% brightness"""
    global PWM_value
    if 0 <= brightness <= 100:
        PWM_value = brightness
        client.publish(PWM_TOPIC, PWM_value)