import board
import busio
import adafruit_mpl3115a2

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
            print("alti error on")
            self.error = True
    
    def altitude(self):
        try:
            return self.sensor.altitude
        except NameError:
            self.error = True
            print('we have an (altimeter) problem')
    
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
    