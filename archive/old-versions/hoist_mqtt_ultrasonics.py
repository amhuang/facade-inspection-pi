
import RPi.GPIO as GPIO
import time
import paho.mqtt.client as paho
import mpu6050 as ACC
import ultrasonics as ULT
#import mpu6050 as ACC # .py in GDrive.
    # Should be either adxl345 or mpu6050
    # See the files for which side faces left/right hoist
import altimeter as ALT
import setInterval as threading

threshold = 3.0 # how much tilt before adjustment
buffer = 1.0    # sec it pauses when past threshold
rest = 0.1      # amt of time between checking angle

''' Motor Setup '''

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

up_left = 19
down_left = 26
up_right = 20
down_right = 21

GPIO.setup(up_left,GPIO.OUT)
GPIO.setup(down_left,GPIO.OUT)
GPIO.setup(up_right,GPIO.OUT)
GPIO.setup(down_right,GPIO.OUT)

broker = "192.168.1.235"    # IP of broker Pi
port = 9001                 # Set in mosquitto.conf

pub_angle = 0   # Just placeholders until on_connect
pub_alti = 0

''' MQTT Setup '''

def on_connect(client, userdata, flags, rc):
    global pub_angle, pub_alti
    pub_angle = setInterval(0.2, publish_angle)
    pub_alti = setInterval(1, publish_all_alti)

def on_subscribe(client, userdata, mid, granted_qos):   #create function for callback
   print("subscribed")
   pass

def on_message(client, userdata, message):
    if message.topic == "hoist":
        msg = message.payload.decode("utf-8")
        print(msg)

        if msg == "off":
            stop()
        elif msg == "up":
            level_up()
        elif msg == "down":
            level_down()

def on_disconnect(client, userdata, rc):
   print("client disconnected")

client = paho.Client("upperPi",transport='websockets')
client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_disconnect = on_disconnect

client.connect(broker,port)
client.subscribe("hoist")
client.loop_start()

''' Accelerometer & Altimeter '''

# Two instances of flask server are running in GUI
# for up and down keys, so we need to skip one of the
# angle publishes or else MQTT gets overwhelmed

def publish_angle():
    try:
        angle = "%.1f" % ACC.angleRaw()
        client.publish("accelerometer/angle", angle)
    except:
        pub_angle.cancel()
        client.publish("accelerometer/angle", "Disconnected")

def publish_all_alti():
    try:
        alt = "%.1f" % ALT.altitude()
        client.publish("altimeter/altitude", alt)

        temp = "%.1f" % ALT.temperature()
        client.publish("altimeter/temperature", temp)

        press = "%.1f" % ALT.pressure()
        client.publish("altimeter/pressure", press)

    except:
        client.publish("altimeter/altitude", "Disconnected")
        client.publish("altimeter/temperature", "Disconnected")
        client.publish("altimeter/pressure", "Disconnected")

def publish_ultrasonic():
    try:
        obst0, obst1 = "%d" % ULT.index()
        client.publish("ultrasonic/upper", obst0)
        time.sleep(0.1)
        client.publish("ultrasonic/lower", obst1)
    except:
        client.publish("ultrasonic", "Disconnected")

'''def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t '''

''' Functions to run and level the hoists '''
def level_up():
    # Makes sure reverse is turned off
    GPIO.output(down_left, GPIO.LOW)
    GPIO.output(down_right, GPIO.LOW)
    GPIO.output(up_left, GPIO.HIGH)
    GPIO.output(up_right, GPIO.HIGH)

    while True:
        # Right side tilted down
        if ACC.angle() > threshold:
            while ACC.angle() > buffer:
                GPIO.output(up_left, GPIO.LOW)
                time.sleep(0.1)
            GPIO.output(up_right, GPIO.HIGH)

        # Left side tilted down
        elif ACC.angle() < -threshold:
            while ACC.angle() < -buffer:
                GPIO.output(up_right, GPIO.LOW)
                time.sleep(0.1)
            GPIO.output(up_left, GPIO.HIGH)

        # Pause before checking again
        time.sleep(0.1)

def level_down():
    # Makes sure forward is turned off
    GPIO.output(up_left, GPIO.LOW)
    GPIO.output(up_right, GPIO.LOW)
    GPIO.output(down_left, GPIO.HIGH)
    GPIO.output(down_right, GPIO.HIGH)

    while True:
        # Right side tilted down
        if ACC.angle() > threshold:
            while ACC.angle() > buffer:
                GPIO.output(down_right, GPIO.LOW)
                time.sleep(0.1)
            GPIO.output(down_right, GPIO.HIGH)

        # Left side tilted down
        elif ACC.angle() < -threshold:
            while ACC.angle() < -buffer:
                GPIO.output(down_left, GPIO.LOW)
                time.sleep(0.1)
            GPIO.output(down_left, GPIO.HIGH)

        # Pause before reading again
        time.sleep(0.1)

def stop():
    GPIO.output(up_left, GPIO.LOW)
    GPIO.output(up_right, GPIO.LOW)
    GPIO.output(down_left, GPIO.LOW)
    GPIO.output(down_right, GPIO.LOW)

publish_ultrasonic()
