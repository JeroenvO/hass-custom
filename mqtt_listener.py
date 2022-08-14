import logging
import os
import signal
import subprocess
from time import sleep

import paho.mqtt.client as paho
import wiringpi as wp

from iofunc import IOFunc, volume
from rgb_light import RGB_Light
from wiringpi_pwm import PWM

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


def on_message(mosq, obj, msg):
    global client
    p = msg.payload.decode('utf-8')
    print("%s %d %s" % (msg.topic, msg.qos, p))
    parts = msg.topic.split('/')
    print(parts)
    if parts[1] == 'switch':
        iof.set_output(int(parts[2]), p)
        # client.publish()
    elif parts[1] == 'light':
        topic = '/'.join(parts[3:])
        light = lights[parts[2]]
        if topic == MQTT_LIGHT_COMMAND_TOPIC:
            light.state = p
            client.publish(f'rpi1/light/{parts[2]}/{MQTT_LIGHT_STATE_TOPIC}', p)
        elif topic == MQTT_LIGHT_RGB_COMMAND_TOPIC:
            light.state = LIGHT_ON
            light.r, light.g, light.b = [int(x)/255.0 for x in p.split(',')]
            client.publish(f'rpi1/light/{parts[2]}/{MQTT_LIGHT_RGB_STATE_TOPIC}', p)
        elif topic == MQTT_LIGHT_BRIGHTNESS_COMMAND_TOPIC:
            light.state = LIGHT_ON
            if p == 0:
                light.state = LIGHT_OFF
                client.publish(f'rpi1/light/{parts[2]}/{MQTT_LIGHT_STATE_TOPIC}', LIGHT_OFF)
            light.brightness = int(p) / 255.0
            client.publish(f'rpi1/light/{parts[2]}/{MQTT_LIGHT_BRIGHTNESS_STATE_TOPIC}', p)
        light.update()

    elif parts[1] == 'display':
        iof.display_write(p)
    elif parts[1] == 'clock':
        if p == 'TOGGLE':
            iof.show_clock()
        else:
            p = int(p)
            if p:
                iof.start_clock()
            else:
                iof.stop_clock()
    elif parts[1] == 'sound':
        iof.set_sound_input(int(p[0]))
    elif parts[1] == 'volume':
        volume(p)

    mosq.publish('pong', 'ack', 0)


def on_publish(mosq, obj, mid):
    # print(f'publish {mosq};{obj};{mid}')
    pass


if __name__ == '__main__':
    client = paho.Client()
    client.on_message = on_message
    client.on_publish = on_publish
    _LOGGER = logging.getLogger(__name__)

    iof = IOFunc()
    lights = {
        'rgb1': RGB_Light(pwm=iof.pwm, client=client, pin_r=1, pin_g=0, pin_b=2),
        'rgb2': RGB_Light(pwm=iof.pwm, client=client, pin_r=3, pin_g=4, pin_b=5),
    }
    iof.display_write('Starting!')
    # client.tls_set('root.ca', certfile='c1.crt', keyfile='c1.key')
    # sleep(1)
    iof.set_output(66, 1)  # enable smart meter 5v, to read data.
    # sleep(1)
    client.connect("127.0.0.1", 1883, 60)

    client.subscribe("rpi1/#", 0)

    while client.loop() == 0:
        pass
