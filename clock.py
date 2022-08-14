#!/usr/bin/python3

__author__ = 'JvO'

# Python Raspberry Pi Domotica
# Jeroen van Oorschot 2014
# Functions that run every minute like alarms and timers

import signal
import os
import subprocess
from time import sleep


def run():
    print("Starting clock")
    volume(20)
    p = subprocess.Popen(['./run_clock.sh', '&'], shell=False, preexec_fn=os.setsid)
    sleep(2)
    for i in range(20, 80, 5):
        volume(i)
        sleep(0.05)
    print('finished volume')
    sleep(10)
    print('turnoff')

    for i in reversed(range(20, 80, 5)):
        sleep(0.05)
        volume(i)
    volume(80)
    os.killpg(os.getpgid(p.pid), signal.SIGTERM)


def volume(vol):
    #    subprocess.call(['amixer', 'sset', 'Master', str(vol)+'%', '-q'], shell=False)
    subprocess.call(['pactl', 'set-sink-volume', '0', str(vol) + '%'])


run()
