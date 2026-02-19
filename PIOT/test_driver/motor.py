import paho.mqtt.client as mqtt

MOTOR_TOPIC = "test/motor" 
motor_speed = 0       


client = mqtt.Client()
client.username_pw_set("user","pokemongo")
client.connect("140.245.45.204", 1883, 60)
client.loop_start()

def init():

    global motor_speed
    motor_speed = 0
    client.publish(MOTOR_TOPIC, motor_speed)

def set_motor_speed(speed):

    global motor_speed
    if 0 <= speed <= 100:
        motor_speed = speed
        client.publish(MOTOR_TOPIC, motor_speed)

def stop():
 
    set_motor_speed(0)
