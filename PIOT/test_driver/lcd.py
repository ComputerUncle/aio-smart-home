import paho.mqtt.client as mqtt

MQTT_TOPIC = "test/lcd"  
class lcd:
    def __init__(self):
        self.lines = [""]*2  


        self.client = mqtt.Client()
        self.client.username_pw_set("user","pokemongo")
        self.client.connect("140.245.45.204", 1883, 60)
        self.client.loop_start()


        self.lcd_clear()

    def _publish(self, action, payload):
        msg = {"action": action, "payload": payload}
        self.client.publish(MQTT_TOPIC, str(msg), retain=True)

    def lcd_display_string(self, string, line=1, pos=0):
        if line < 1 or line > 2:
            return
        string_display = string[:16].ljust(16)
        self.lines[line-1] = string_display
        self._publish("display_string", {"line": line, "pos": pos, "text": string_display})

    def lcd_clear(self):
        self.lines = [""]*2
        self._publish("clear", {})
