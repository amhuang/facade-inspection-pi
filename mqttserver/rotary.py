
from RPi import GPIO
from time import sleep
import math

clk = 17
dt = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
counter = 0
clkLastState = GPIO.input(clk)

r = 0.1 #radius in m

try:
    while True:
        clkState = GPIO.input(clk)
        if clkState != clkLastState:
            dtState = GPIO.input(dt)
            if dtState != clkState:
                counter += 1
                print("going up")
            else:
                counter -= 1
                print("going down")
            #print(counter)
            distance = 2*math.pi*r*counter/30
            print(distance)
        clkLastState = clkState
        sleep(0.01)
finally:
    GPIO.cleanup()