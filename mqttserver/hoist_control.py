import RPi.GPIO as GPIO
import time
import mpu6050
from timer import Timer
import threading

''' GPIO & Motor Setup '''

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

UP_L, DOWN_L = 19, 26
UP_R, DOWN_R = 20, 21

GPIO.setup(UP_L,GPIO.OUT)
GPIO.setup(DOWN_L,GPIO.OUT)
GPIO.setup(UP_R,GPIO.OUT)
GPIO.setup(DOWN_R,GPIO.OUT)

threshold = 1.5  # how much tilt before adjustment
buffer = 0.5    # angle adjusted to while leveling
max_time = 1

time_from_ground = Timer()
timer_exec = Timer()

''' Calculating Angle '''

ACC = mpu6050.ACC(offset=0)

def set_offset(off):
    ACC.offset = off
    print("hoist offset: ", ACC.offset)

def set_time(init_time):
    global time_from_ground
    time_from_ground = Timer()
    time_from_ground.start_from(init_time)

'''
Functions that turn turn both or just one hoist. They turn off
every other hoist or direction that's not being used.
'''

def stop():
    GPIO.output(UP_L, GPIO.LOW)
    GPIO.output(UP_R, GPIO.LOW)
    GPIO.output(DOWN_L, GPIO.LOW)
    GPIO.output(DOWN_R, GPIO.LOW)
    time_from_ground.pause()

def up_both():
    time_from_ground.pause()
    GPIO.output(DOWN_L, GPIO.LOW)
    GPIO.output(DOWN_R, GPIO.LOW)
    GPIO.output(UP_L, GPIO.HIGH)
    GPIO.output(UP_R, GPIO.HIGH)
    time_from_ground.start_countup()

def down_both():
    time_from_ground.pause()
    GPIO.output(UP_L, GPIO.LOW)
    GPIO.output(UP_R, GPIO.LOW)
    GPIO.output(DOWN_L, GPIO.HIGH)
    GPIO.output(DOWN_R, GPIO.HIGH)
    time_from_ground.start_countdown()

def up_left():
    time_from_ground.pause()
    GPIO.output(DOWN_L, GPIO.LOW)
    GPIO.output(DOWN_R, GPIO.LOW)
    GPIO.output(UP_R, GPIO.LOW)
    GPIO.output(UP_L, GPIO.HIGH)
    time_from_ground.start_countup("half")

def up_right():
    time_from_ground.pause()
    GPIO.output(DOWN_L, GPIO.LOW)
    GPIO.output(DOWN_R, GPIO.LOW)
    GPIO.output(UP_L, GPIO.LOW)
    GPIO.output(UP_R, GPIO.HIGH)
    time_from_ground.start_countup("half")

def down_left():
    time_from_ground.pause()
    GPIO.output(UP_R, GPIO.LOW)
    GPIO.output(UP_L, GPIO.LOW)
    GPIO.output(DOWN_R, GPIO.LOW)
    GPIO.output(DOWN_L, GPIO.HIGH)
    time_from_ground.start_countdown("half")

def down_right():
    time_from_ground.pause()
    GPIO.output(UP_R, GPIO.LOW)
    GPIO.output(UP_L, GPIO.LOW)
    GPIO.output(DOWN_L, GPIO.LOW)
    GPIO.output(DOWN_R, GPIO.HIGH)
    time_from_ground.start_countdown("half")


'''
Leveling algorithm for control of both hoists
If the angle is outside of a threshold range, this algorithm
levels the hoist up until a certain buffer angle (undershoot).
When within the threshold range, both hoists are on. These
functions are meant to be called in in intervals
'''

def level_up():
    global max_time
    timer = Timer()
    try:
        angle = ACC.angle()

        # Right side tilted down
        if angle > threshold:
            while (angle > buffer) and (timer.countup() < max_time):
                angle = ACC.angle()
                up_right()
                print("left stopped: " , angle)
                # No sleep here bc ACC.angle takes 0.1-0.2s to run
            up_both()

        # Left side tilted down
        elif angle < -threshold:
            while (angle < -buffer) and (timer.countup() < max_time):
                angle = ACC.angle()
                up_left()
                print("right stopped: ", angle)
            up_both()

        else:
            up_both()

    except:
        stop()

def level_down():
    global max_time
    timer = Timer()

    try:
        angle = ACC.angle()

        # Right side tilted down
        if angle > threshold:
            while (angle > buffer) and (timer.countup() < max_time):
                angle = ACC.angle()
                down_left()
                print("right stopped: ", angle)
                # No sleep here bc ACC.angle takes 0.1-0.2s to run
            down_both()

        # Left side tilted down
        elif angle < -threshold:
            while (angle < -buffer) and (timer.countup() < max_time):
                angle = ACC.angle()
                down_right()
                print("left stopped: ", angle)
            down_both()

        else:
            down_both()

    except:
        stop()

def make_level():
    timer = Timer()
    max_time = 3

    try:
        angle = ACC.angle()

        # Right side tilted down
        if angle > threshold:
            while (angle > buffer) and (timer.countup() < max_time):
                angle = ACC.angle()
                down_left()
                print("left moving: ", angle)
            stop()

        # Left side tilted down
        elif angle < -threshold:
            while (angle < -buffer) and (timer.countup() < max_time):
                angle = ACC.angle()
                down_right()
                print("right moving: ", angle)
            stop()

    except:
        stop()
