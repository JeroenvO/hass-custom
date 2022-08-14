
# inspired by https://github.com/smrtnt/Open-Home-Automation/blob/master/ha_mqtt_rgb_light/ha_mqtt_rgb_light.ino

MQTT_LIGHT_STATE_TOPIC = "light/status"
MQTT_LIGHT_COMMAND_TOPIC = "light/switch"

# brightness
MQTT_LIGHT_BRIGHTNESS_STATE_TOPIC = "brightness/status"
MQTT_LIGHT_BRIGHTNESS_COMMAND_TOPIC = "brightness/set"

# colors(rgb)
MQTT_LIGHT_RGB_STATE_TOPIC = "rgb/status"
MQTT_LIGHT_RGB_COMMAND_TOPIC = "rgb/set"

# payloads
LIGHT_ON = "ON"
LIGHT_OFF = "OFF"

class RGB_Light:
    def __init__(self, pwm, client):
        """

        :param pwm: PWM device of wiringpi
        :param client: PAHO MQTT client
        """
        self.pwm = pwm
        self.client = client
        self.r = 0
        self.g = 0
        self.b = 0
        self.brightness = 0
        self.state = LIGHT_OFF
        self.pin_r = None
        self.pin_g = None
        self.pin_b = None


    # set the dutycycle of a pwm output
    def set_pwm(self, pin, dc):
        self.pwm.setPWM(pin, dc * 4096.0)

    def set_color(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
        self.update()

    def set_brightness(self, brightness):
        self.brightness = brightness
        self.update()

    def set_brightness(self, brightness):
        self.brightness = brightness
        self.update()

    def update(self):
        if self.state == LIGHT_ON:
            self.set_pwm(self.pin_r, self.r*self.brightness)
            self.set_pwm(self.pin_g, self.g*self.brightness)
            self.set_pwm(self.pin_b, self.b*self.brightness)
        else:
            self.set_pwm(self.pin_r, 0)
            self.set_pwm(self.pin_g, 0)
            self.set_pwm(self.pin_b, 0)

    def callback(self, topic, payload):
        print(f'Topic: {topic}. Payload: {payload}')
        if topic == MQTT_LIGHT_COMMAND_TOPIC:
            self.state = payload
            self.update()
