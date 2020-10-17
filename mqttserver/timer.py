import time
import threading
from threading import Timer

class Timer:
    def __init__(self):
        self._start_time = None
        self._marker = None
        self._marker_tmp = None
        
        self.curr = 0.0
        self.interval = 0.1
        
        self.stopEvent = threading.Event()
        self.threadUp = None
        self.threadDown = None
        
    # Starts the timer. Called in countup and countdown
    def start(self):
        self._start_time = time.perf_counter()
    
    # Starts the timer given a starting num of seconds
    def start_from(self, init_time):
        self.curr = init_time
        self._marker = time.perf_counter()
        self._start_time = self._marker - self.curr
        
    # Returns time btwn when this func is called and start_time
    def countup(self):
        if self._start_time is None:
            self.start()
            
        self._marker = time.perf_counter()
        self.curr = round(self._marker - self._start_time, 2)
        return self.curr
    
    def countup_half(self):
        if self._start_time is None:
            self.start()
        
        self._marker_tmp = time.perf_counter()
        diff = self._marker_tmp - self._marker
        self._start_time += diff/2
        self._marker = self._marker_tmp
        self.curr = round(self._marker - self._start_time, 2)
        return self.curr
    
    # Counts down from _marker
    def countdown(self):
        if self._start_time is None:
            self.start()
            
        if self._marker is None:
            self._marker = self._start_time
            
        #pushes forward temporary marker
        self._marker_tmp = time.perf_counter()
        
        # takes diff btwn tmp and marker and moves starttime up by that much
        diff = self._marker_tmp - self._marker
        self._start_time += 2 * diff
        self._marker = self._marker_tmp
        self.curr = round(self._marker - self._start_time, 2)
        return self.curr
    
    def countdown_half(self):
        if self._start_time is None:
            self.start()
            
        if self._marker is None:
            self._marker = self._start_time
            
        #pushes forward temporary marker
        self._marker_tmp = time.perf_counter()
        
        # takes diff btwn tmp and marker and moves starttime up by that much
        diff = self._marker_tmp - self._marker
        self._start_time += 1.5 * diff
        self._marker = self._marker_tmp
        self.curr = round(self._marker - self._start_time, 2)
        return self.curr
    
    # Start threads that refresh self.curr every 0.1s
    def __interval(self, action) :
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()) :
            nextTime += self.interval
            action()
    
    # Starts a countup thread 
    def start_countup(self, rate="normal"):
        if (self._start_time is None) or (self._marker is None):
            self.countup()
        else:
            self._marker = time.perf_counter()
            self._start_time = self._marker - self.curr
            
        if rate == "half":
            self.threadUp = threading.Thread(target=self.__interval, args=(self.countup_half,))
        else:
            self.threadUp = threading.Thread(target=self.__interval, args=(self.countup,))
        
        self.stopEvent.clear()
        self.threadUp.start()
    
    def start_countdown(self, rate="normal"):
        if (self._start_time is None) or (self._marker is None):
            self.countdown()
        else:
            self._marker = time.perf_counter()
            self._start_time = self._marker - self.curr
        
        if rate == "half":
            self.threadDown = threading.Thread(target=self.__interval, args=(self.countdown_half,))
        else:
            self.threadDown = threading.Thread(target=self.__interval, args=(self.countdown,))
            
        self.stopEvent.clear()
        self.threadDown.start()
        
    def pause(self):
        #self.curr = self.countup()
        self.stopEvent.set()
        if self.threadUp is not None:
            self.threadUp.join()
        if self.threadDown is not None:
            self.threadDown.join()

class setInterval:
    def __init__(self, interval, action) :
        self.interval = interval
        self.action = action
        self.stopEvent = threading.Event()
        self.thread = threading.Thread(target=self.__setInterval)

    def __setInterval(self) :
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()) :
            nextTime += self.interval
            self.action()

    def start(self) :
        self.thread.start();

    def cancel(self) :
        self.stopEvent.set()

'''
hi = Timer()
hi.start_from(20)
hi.start_countdown("half")

while True:
    print(hi.curr)
    time.sleep(.2)
    print(hi.curr)
    time.sleep(.2)
    print(hi.curr)
    time.sleep(.2)
    print(hi.curr)
    time.sleep(.2)
    hi.pause()
    hi.start_countdown()
'''
