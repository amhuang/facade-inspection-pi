import board
import busio
import adafruit_bmp280
import time
import timer
import numpy as np

# create library object using our Bus SPI port
i2c = busio.I2C(board.SCL, board.SDA)

class ALT:
    def __init__(self, sea_level):
        self.error = False
        self.offset = 0

        try:
            #
            self.bmp_280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
            self.bmp_280.sea_level_pressure = sea_level
        except:
            self.error = True

    def zero_height(self):
        try:
            self.offset = self.bmp_280.altitude
        except:
            print("zero height failed")

    def altitude(self):
        #try:
        t = timer.Timer()
        t.start()
        count = 0
        lst = np.empty(0)
        while (t.countup() < 0.45):
            lst = np.insert(lst, count, self.altitude_raw())
            count += 1
        return np.mean(lst) - self.offset
        #except:
        #    self.error = True

    def altitude_raw(self):
        try:
            return self.bmp_280.altitude
        except:
            self.error = True
            print("failed to take altitude")

def pressure():
    return bmp_280.pressure

def temperature():
    celcius = bmp_280.temperature
    fahr = (celcius * (9/5)) + 32
    return fahr

def print_readings():
    celcius = bmp_280.temperature
    fahr = (celcius * (9/5)) + 32
    print("\nTemperature: %0.1f F" % fahr)
    print("Pressure: %0.1f hPa" % bmp_280.pressure)
    print("Altitude = %0.2f meters" % bmp_280.altitude)

'''
hi = ALT(1015)
while True:
    print(hi.altitude())
'''
