'''  Neg angle when side with VCC/GN (LEFT hoist) is lower
Pos angle when side with INT/ADD (RIGHT hoist) is lower '''

import smbus
import math
import time
import timer
import numpy as np

offset = 0

# Register
power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c

def read_byte(reg):
    return bus.read_byte_data(address, reg)

def read_word(reg):
    h = bus.read_byte_data(address, reg)
    l = bus.read_byte_data(address, reg+1)
    value = (h << 8) + l
    return value

def read_word_2c(reg):
    val = read_word(reg)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val

def dist(a,b):
    return math.sqrt((a*a)+(b*b))

def pitch(x,y,z):
    radians = math.atan2(y, dist(x,z))
    return math.degrees(radians)

def roll(x,y,z):
    radians = math.atan2(x, dist(y,z))
    return -math.degrees(radians)

bus = smbus.SMBus(1) # bus = smbus.SMBus(0) fuer Revision 1
address = 0x68       # via i2cdetect


# Scaled gyro readings by 131
def scale_gyro():
    gyro_xout = read_word_2c(0x43) / 131
    gyro_yout = read_word_2c(0x45) / 131
    gyro_zout = read_word_2c(0x47) / 131
    return (gyro_xout, gyro_yout, gyro_zout)

def scale_accel():
    accel_xout = read_word_2c(0x3b) / 16384.0
    accel_yout = read_word_2c(0x3d) / 16384.0
    accel_zout = read_word_2c(0x3f) / 16384.0
    return (accel_xout, accel_yout, accel_zout)

class ACC:
    def __init__(self, offset):
        self.offset = offset
        self.error = False
        try:
            # Activate to be able to address the module
            bus.write_byte_data(address, power_mgmt_1, 0)
        except OSError:
            self.error = True
    
    def angle_raw(self):
        try:
            acceleration = scale_accel()
            self.error = False
            
            x = acceleration[0]
            y = acceleration[1]
            z = acceleration[2]

            return pitch(x,y,z)
        
        except OSError:
            self.error = True
            print('we have an (accelerometer) problem')
        

    def angle(self):
        t = timer.Timer()
        t.start()
        count = 0
        lst = np.empty(0)
        while (t.countup() < .1):
            lst = np.insert(lst, count, self.angle_raw())
            count += 1
        return np.mean(lst) - self.offset


hi = ACC(-1)

while True:
    start = time.time()
    angle = hi.angle()
    print(angle)
    stop = time.time()
    print("time = ", stop - start)
