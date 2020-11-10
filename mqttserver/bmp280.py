import board
import busio
import adafruit_bmp280
import time
from timer import Timer
import numpy as np

# create library object using our Bus SPI port
i2c = busio.I2C(board.SCL, board.SDA)

class ALT:
    def __init__(self, sea_level):

        self.error = False
        self.offset = 0
        
        try:
            # Activate to be able to address the module
            self.bmp_280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
            # change this to match the location's pressure (hPa) at sea level
            self.bmp_280.sea_level_pressure = sea_level
        except:
            self.error = True
            
    def zero_height(self):
        try:
            self.offset = self.bmp_280.altitude
        except:
            print("zero height failed")
    
    def altitude(self):
        try: 
            timer = Timer().start()
            count = 0
            lst = np.empty(0)
            while (timer.countup() < .45):
                alt = self.bmp_280.altitude - self.offset
                lst = np.insert(lst, count, alt)
                count += 1
            return np.mean(lst)
        except:
            self.error = True
            #print('we have an (altimeter) problem')

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
