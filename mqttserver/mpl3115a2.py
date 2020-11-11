import board
import busio
import adafruit_mpl3115a2
import timer
import numpy as np

i2c = busio.I2C(board.SCL, board.SDA)
#sensor.sealevel_pressure = 101592

class ALT:
    def __init__(self, sea_level):
        self.error = False
        self.offset = 0

        try:
            # Activate to be able to address the module
            self.sensor = adafruit_mpl3115a2.MPL3115A2(i2c)
            # change this to match the location's pressure (hPa) at sea level
            self.sensor.sealevel_pressure = sea_level*100
        except:
            self.error = True

    def altitude(self):
        try:
            t = timer.Timer()
            t.start()
            count = 0
            lst = np.empty(0)
            while (t.countup() < 1):
                lst = np.insert(lst, count, self.altitude_raw())
                count += 1
            return np.mean(lst) - self.offset
        except:
            self.error = True

    def alitude_raw(self):
        try:
            return self.sensor.altitude
        except:
            self.error = True
            print("problem taking angle")

    def zero_height(self):
        try:
            self.offset = self.sensor.altitude
        except:
            print("zero height failed")

def altitude():
    return sensor.altitude

def temperature():
    return sensor.temperature

def pressure():
    return sensor.pressure/3386.29

def sealevel_pressure(self, inhg):
    self.sensor.sealevel_pressure = inhg
