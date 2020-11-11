''' Pos angle when side with VIN/GND (RIGHT hoist) is lower
Neg angle when side with SDA/SCL (LEFT hoist) is lower '''

import board
import busio
import math
import time
import adafruit_adxl34x
i2c = busio.I2C(board.SCL, board.SDA)
adxl = adafruit_adxl34x.ADXL345(i2c)

fx = 0
fy = 0
fz = 0
offset = 0

def angleRaw():
    acceleration = read()
    offset = 1  # hard calibrated for our chip since the soldering is not completely flat
    x = acceleration[0]
    y = acceleration[1]
    z = acceleration[2]
    return pitch(x,y,z) - offset

def angleOffset():
    global offset
    acceleration = read()
    x = acceleration[0]
    y = acceleration[1]
    z = acceleration[2]

    # First reading stored as offset to adjust subsequent readings
    if offset == 0:
        offset = pitch(x, y, z)
        return 0
    else:
        return pitch(x,y,z) - offset

# Rotation in x dir
def pitch(x, y, z):
    return (math.atan2(x, math.sqrt(y*y + z*z))*180)/math.pi

# Rotation in y dir
def roll(x, y, z):
    return (math.atan2(-y, z)*180)/math.pi

# Reads raw acceleration data and returned smoothed data
def read():
    global fx, fy, fz
    alpha = .5
    acceleration = adxl.acceleration
    x = acceleration[0] # pitch
    y = acceleration[1] # roll
    z = acceleration[2] # yaw

    # Low pass filter (smoothing factor alpha)
    fx = x*alpha + (fx*(1.0-alpha))
    fy = y*alpha + (fy*(1.0-alpha))
    fz = z*alpha + (fz*(1.0-alpha))
    return (fx,fy,fz)