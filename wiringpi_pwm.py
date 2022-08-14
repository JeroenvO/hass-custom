import wiringpi as wp
import time, math, struct

class PWM(object):
    i2c = None

    # Registers/etc.
    __MODE1              = 0x00
    __MODE2              = 0x01
    __SUBADR1            = 0x02
    __SUBADR2            = 0x03
    __SUBADR3            = 0x04
    __PRESCALE           = 0xFE
    __LED0_ON_L          = 0x06
    __LED0_ON_H          = 0x07
    __LED0_OFF_L         = 0x08
    __LED0_OFF_H         = 0x09
    __ALL_LED_ON_L       = 0xFA
    __ALL_LED_ON_H       = 0xFB
    __ALL_LED_OFF_L      = 0xFC
    __ALL_LED_OFF_H      = 0xFD

  # Bits
    __RESTART            = 0x80
    __SLEEP              = 0x10
    __ALLCALL            = 0x01
    __INVRT              = 0x10
    __OUTDRV             = 0x04

    @staticmethod
    def getPiI2CBusNumber():
        """
        Returns the I2C bus number (/dev/i2c-#) for the Raspberry Pi being used.

        Courtesy quick2wire-python-api
        https://github.com/quick2wire/quick2wire-python-api
        """
        try:
            with open('/proc/cpuinfo','r') as f:
                for line in f:
                    if line.startswith('Revision'):
                        return 1
        except:
            return 0

    @staticmethod
    def sanitize_int(x):
        if x < 0:
            return 0
        elif x > 4095:
            return 4095
        else:
            return int(x)

    def __init__(self, address=0x40, debug=False):
        """
        Setup a Pulse-Width Modulation object, for controlling an I2C device.

        Parameters
        address: The address of the I2C device in hex.
                 Find using `i2cdetect -y [0|1]`
        debug: Boolean value specifying whether or not to print debug messages.
        """
        wp.wiringPiSetupSys()
        self.i2c = wp.I2C()
        self.fd = self.i2c.setupInterface('/dev/i2c-' + str(PWM.getPiI2CBusNumber()), address)
        self.address = address
        self.debug = debug
        if (self.debug):
            print("Got an fd: %d" % self.fd)
            print("Reseting PCA9685")
        self.setAllPWM(0, 0)
        #self.i2c.writeReg8(self.fd, self.__MODE1, 0x00)
        self.i2c.writeReg8(self.fd, self.__MODE2, self.__OUTDRV) #set as totempole
        ###############test###self.i2c.writeReg8(self.fd, self.__MODE2, self.__INVRT) #set non-inverted
        #self.i2c.writeReg8(self.fd, self.__MODE1, self.__ALLCALL)
        time.sleep(0.005)                                       # wait for oscillator

        mode1 = self.i2c.readReg8(self.fd, self.__MODE1)
        mode1 = mode1 & ~self.__SLEEP                 # wake up (reset sleep)
        self.i2c.writeReg8(self.fd, self.__MODE1, mode1)
        time.sleep(0.005)

    def setPWMFreq(self, freq):
        """
        Sets the PWM frequency.

        Parameters
        freq: The frequency (int) in hz.
        """
        prescaleval = 25000000.0 # 25MHz
        prescaleval /= 4096.0    # 12-bit
        prescaleval /= float(freq)
        prescaleval -= 1.0
        if (self.debug):
            print("Setting PWM frequency to %d Hz" % freq)
            print("Estimated pre-scale: %d" % prescaleval)
        prescale = math.floor(prescaleval + 0.5)
        if (self.debug):
            print("Final pre-scale: %d" % prescale)

        oldmode = self.i2c.readReg8(self.fd, self.__MODE1);
        newmode = (oldmode & 0x7F) | 0x10 # sleep
        if (self.debug):
            print("oldmode: %d" % oldmode)
            print("newmode: %d" % newmode)
        self.i2c.writeReg8(self.fd, self.__MODE1, newmode) # go to sleep
        self.i2c.writeReg8(self.fd, self.__PRESCALE, int(math.floor(prescale)))
        self.i2c.writeReg8(self.fd, self.__MODE1, oldmode)
        time.sleep(0.005)
        self.i2c.writeReg8(self.fd, self.__MODE1, oldmode | 0x80)

    def setPWM(self, channel, val):
        """
        Sets a single PWM channel.

        Parameters
        channel: The channel (int)
        val: The value to set it to. Between 0 and 4095.
        """
        val = self.sanitize_int(val)
        self.i2c.writeReg8(self.fd, self.__LED0_ON_L+4*channel, 0)
        self.i2c.writeReg8(self.fd, self.__LED0_ON_H+4*channel, 0)
        self.i2c.writeReg8(self.fd, self.__LED0_OFF_L + 4 * channel, val & 0xFF)
        self.i2c.writeReg8(self.fd, self.__LED0_OFF_H + 4 * channel, val >> 8)

    def setAllPWM(self, on, off):
        "Sets a all PWM channels"
        self.i2c.writeReg8(self.fd, self.__ALL_LED_ON_L, on & 0xFF)
        self.i2c.writeReg8(self.fd, self.__ALL_LED_ON_H, on >> 8)
        self.i2c.writeReg8(self.fd, self.__ALL_LED_OFF_L, off & 0xFF)
        self.i2c.writeReg8(self.fd, self.__ALL_LED_OFF_H, off >> 8)

    def readPWM(self, channel):
        """
        Returns the value of a single PWM channel.

        Parameters
        channel: The channel (int)
        """
        low  = self.i2c.readReg8(self.fd, self.__LED0_OFF_L + 4 * channel)
        high = self.i2c.readReg8(self.fd, self.__LED0_OFF_H + 4 * channel)
        return (high << 8) + low
