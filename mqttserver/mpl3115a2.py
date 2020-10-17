import board
import busio
import adafruit_mpl3115a2

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_mpl3115a2.MPL3115A2(i2c)
sensor.sealevel_pressure = 101592
    
def altitude():
    return sensor.altitude

def temperature():
    return sensor.temperature

def pressure():
    return sensor.pressure/3386.29

def sealevel_pressure(self, inhg):
    self.sensor.sealevel_pressure = inhg

'''
while True:
    print(altitude())
    print(pressure())
    '''