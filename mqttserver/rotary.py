from RPi import GPIO
import time
import math
import timer

GPIO.setmode(GPIO.BCM)
clk = 17
dt = 27
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

class Rotary:
    def __init__(self, r):
        self.dist = 0         # This should be in feet
        self.r = r
        self.rotary_count = 0
        self.clk_prev = GPIO.input(clk)
        self.thread = timer.setInterval(0.002, self.height)
        self.thread.start()
        
    
    def zero_height(self):
        self.dist = 0
        self.rotary_count = 0
    
    def height(self):
        clk_curr = GPIO.input(clk)
        
        if clk_curr != self.clk_prev:
            dt_curr = GPIO.input(dt)
            if dt_curr != clk_curr:
                self.rotary_count += 1
            else:
                self.rotary_count -= 1
            self.dist = (2 * math.pi *self.r) * 3.28 * (self.rotary_count/30)
            self.clk_prev = clk_curr

'''
hi = Rotary(0.1)
while True:
    print(hi.rotary_count)
    time.sleep(0.1)
'''

'''
clk_prev = GPIO.input(clk)

r = 0.1 #radius in m
rotary_count = 0

try:
    while True:
        clk_curr = GPIO.input(clk)
        if clk_curr != clk_prev:
            dt_curr = GPIO.input(dt)
            if dt_curr != clk_curr:
                rotary_count += 1
                print("going up")
            else:
                rotary_count -= 1
                print("going down")
            print(rotary_count)
            distance = 2*math.pi*r*rotary_count/30
            print(distance)
        clk_prev = clk_curr
        sleep(0.01)
finally:
    GPIO.cleanup()
'''