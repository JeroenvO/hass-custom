#!/usr/bin/env python

import logging
import os
import signal
import subprocess
from time import sleep

import paho.mqtt.client as paho
import wiringpi as wp

from rgb_light import RGB_Light
from wiringpi_pwm import PWM

OUTPUT = 1
INPUT = 0
PUD_UP = 2  # pull up resistor
OUTPUT_PINS_0 = [0, 1, 4, 5, 7]  # rpi pins, in wiringpi pinmapping
PB1 = 64  # pinbase for first (audio and display) expander
PB2 = 16 + PB1  # pinbase for relay control expander
OUTPUT_PINS_1 = [64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79]
INPUT_PINS_1 = []

OUTPUT_PINS_2 = [80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95]
INPUT_PINS_2 = []
MIN_VOLUME = 20
MAX_VOLUME = 70


class IOFunc():
    def __init__(self):
        wp.wiringPiSetup()

        for pin in OUTPUT_PINS_0:
            wp.pinMode(pin, OUTPUT)

        # left 23017, for audio
        wp.mcp23017Setup(PB1, 0x20)
        for pin in OUTPUT_PINS_1:
            wp.pinMode(pin, OUTPUT)
        for pin in INPUT_PINS_1:
            wp.pinMode(pin, INPUT)

        # right 23017 for 230v switching
        wp.mcp23017Setup(PB2, 0x21)
        for pin in OUTPUT_PINS_2:
            wp.pinMode(pin, OUTPUT)
        for pin in INPUT_PINS_2:
            wp.pullUpDnControl(pin, PUD_UP)
            wp.pinMode(pin, INPUT)
        # display
        wp.digitalWrite(70, 0)  # display_write mode
        self.display1 = wp.lcdInit(2, 16, 8, 71, 69, 72, 73, 74, 75, 76, 77, 78, 79)  # connected to first expander
        wp.lcdClear(self.display1)
        self.p = None  # clock process

        self.pwm = PWM(address=0x40)
        self.pwm.setPWMFreq(200)

    def set_sound_input(self, channel):
        if channel > 3 or channel < 0:  # impossible channels
            return False

        if channel == 0:
            channel = 3  # set channel to raspberry
            self.set_output(95, 0)  # disable amplifier
        else:
            self.set_output(95, 1)  # enable amplifier

        channel = bin(channel)

        if len(channel) < 4:  # channel == 1 or == 0
            bit0 = 0
            bit1 = 1
        else:
            bit0 = int(channel[2])
            bit1 = int(channel[3])
        wp.digitalWrite(PB1 + 0, bit1)
        wp.digitalWrite(PB1 + 1, bit0)

    # clean the display and display_write a string
    def display_write(self, string):
        string = string[0:32]
        wp.lcdClear(self.display1)
        wp.lcdHome(self.display1)
        wp.lcdPrintf(self.display1, string)

    def set_output(self, pin, value):
        """
        Set an io output on or of

        :param pin: pin number (int)
        :param value: trueish or falseish
        :return:
        """
        if pin in OUTPUT_PINS_1 or pin in OUTPUT_PINS_2 or pin in OUTPUT_PINS_0:
            value = int(value)
            print(pin, value)
            wp.digitalWrite(pin, value)

    def start_clock(self):
        if self.p:
            print('stop clock {}'.format(self.p))
            os.killpg(os.getpgid(self.p.pid), signal.SIGINT)
            sleep(1)
            os.killpg(os.getpgid(self.p.pid), signal.SIGTERM)
        print('starting clock')
        self.p = subprocess.Popen(['./run_clock.sh'], shell=True, preexec_fn=os.setsid)
        print('started clock {}'.format(self.p))
        for i in range(MIN_VOLUME, MAX_VOLUME, 5):
            volume(i)
            sleep(0.05)
        print('finish start clock')

    def stop_clock(self):
        print('f stop clock')
        if self.p:
            print('stop clock {}'.format(self.p))
            for i in reversed(range(MIN_VOLUME, MAX_VOLUME, 5)):
                volume(i)
                sleep(0.05)
            os.killpg(os.getpgid(self.p.pid), signal.SIGINT)
            sleep(0.4)
            os.killpg(os.getpgid(self.p.pid), signal.SIGTERM)
        print('finish stop clock')


def volume(vol):
    subprocess.call(['amixer', '-c', '1', '-q', 'sset', 'Speaker', str(vol) + '%'], shell=False)
    # subprocess.call(['pactl', 'set-sink-volume', '0', str(vol) + '%'])

