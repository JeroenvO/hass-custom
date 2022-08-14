#!/bin/bash
# See https://github.com/JeroenvO/scopeclock
 ../scopeclock/scopeclock | aplay -f U8 -c 2 -r 48000 -D sysdefault:CARD=Device
