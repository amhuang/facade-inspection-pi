'''
Upper Pi MQTT Client

Runs two hoists, publishes and collects accelerometer and time data.
'''

import RPi.GPIO as GPIO
import time
import paho.mqtt.client as paho
import subprocess
#import setInterval as thread
import mpu6050
import hoist_control as HOIST
import timer

''' Setup & Global Variables '''

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

UP_L, DOWN_L = 19, 26
UP_R, DOWN_R = 20, 21

GPIO.setup(UP_L,GPIO.OUT)
GPIO.setup(DOWN_L,GPIO.OUT)
GPIO.setup(UP_R,GPIO.OUT)
GPIO.setup(DOWN_R,GPIO.OUT)

angle_error_count = 0
ACC = mpu6050.ACC(offset=0)
ignore_angle = False

last_msg_timer = timer.Timer()

'''
MQTT Setup
'''
#getip = subprocess.Popen(['hostname', '-I'], stdout=subprocess.PIPE)
#broker = getip.stdout.read().decode('utf-8')    # IP of broker Pi
broker = "192.168.1.235"
port = 9001                 # Set in mosquitto.conf
topic, msg = '', ''

def on_connect(client, userdata, flags, rc):
    global angle_thread, timefromground_thread, ignore_angle, acc_err_thread
        
    client.subscribe("hoist")
    client.subscribe("time/fromground")
    client.subscribe("accelerometer/status")
    print("connected")
    
    timefromground_thread = timer.setInterval(5, publish_timefromground)
    timefromground_thread.start()
    acc_err_thread = timer.setInterval(.5, accel_disconnect)
    
    if ACC.error == True:
        ignore_angle = True
        acc_err_thread.start()
    else:
        angle_thread = timer.setInterval(0.25, publish_angle)
        angle_thread.start()

def on_message(client, userdata, message):
    global topic, msg
    topic = message.topic
    msg = message.payload.decode("utf-8")
    last_msg_timer.start()

def on_disconnect(client, userdata, rc):
    global angle_thread, broker, port
    HOIST.stop()
    try:
        angle_thread.cancel()
    except NameError:
        pass
    print("client disconnected. Reason code", rc)
    client.connect(broker, port, keepalive=3)

'''
Processing and publishing data
'''

angle_lst = [0,1,2,3,4,5]  # keeps track of prev angles
angle_i = 0

def publish_angle():
    global angle_thread, angle_lst, angle_i, angle_error_count
    if ACC.error == False:
        if (angle_i == 6):
            angle_i = 0

        angle = ACC.angle()
        angle_lst[angle_i] = angle
        angle_i += 1

        if (all_same(angle_lst)):
            stop()
            print("all same - accelerometer disconnected")
            client.publish("accelerometer/status", "Disconnected")
            angle_thread.cancel()
            return

        client.publish("accelerometer/angle", angle)
        angle_error_count = 0

    else:
        accel_disconnect("retry")

def accel_disconnect(recourse="now"):
    global angle_error_count, angle_thread, acc_err_thread
    
    if recourse == "retry":
        angle_error_count += 1

        # Stops publishing accel data if disconnected for over 1sec
        if angle_error_count == 10:
            HOIST.stop()
            angle_thread.cancel()
            print("accelerometer disconnect 1s")
            client.publish("accelerometer/status", "Disconnected")
        return
    
    else:
        client.publish("accelerometer/status", "Disconnected")

def all_same(lst):
    return not lst or lst.count(lst[0]) == len(lst)

def publish_timefromground():
    client.publish('time/fromground', str(HOIST.time_from_ground.curr))


'''
Creates MQTT client & runs client loop
'''

clientID = "upper" + str(time.time())
client = paho.Client(clientID, transport='websockets')
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

client.will_set("status", "Upper Pi client disconnected", retain=False)
client.connect(broker, port, keepalive=5)

try:
    while True:
        client.loop_start()

        if (last_msg_timer.countup() >= 1 or HOIST.time_from_ground.curr <= -5):
            # timer starts in on_message received
            HOIST.stop()

        elif topic == "hoist":
            print(msg)

            if msg == "Off":
                HOIST.stop()

            elif msg == "Switch to backup":
                publish_timefromground()
                client.unsubscribe("hoist")
                client.unsubscribe("time/fromground")
                client.unsubscribe("accelerometer/status")
                try:
                    acc_err_thread.cancel()
                    timefromground_thread.cancel()
                    angle_thread.cancel()
                except NameError:
                    pass
                
            elif msg == "Disable leveling":
                ignore_angle = True
                try:
                    acc_err_thread.cancel()
                except NameError:
                    pass

            elif msg == "Make level":
                HOIST.make_level()

            elif msg == "Toggle leveling" and ACC.error == False:
                if ignore_angle:
                    ignore_angle = False
                else:
                    ignore_angle = True

            elif msg == "Up":
                if ignore_angle:
                    HOIST.up_both()
                else:
                    HOIST.level_up()

            elif msg == "Down":
                if ignore_angle:
                    HOIST.down_both()
                else:
                    HOIST.level_down()

            elif msg == "Up left":
                HOIST.up_left()

            elif msg == "Up right":
                HOIST.up_right()

            elif msg == "Down left":
                HOIST.down_left()

            elif msg == "Down right":
                    HOIST.down_right()

        elif topic == "accelerometer/status":

            if msg == "Zero accelerometer":
                ACC.offset = ACC.angle_raw()
                HOIST.set_offset(ACC.offset)
                print("Accelerometer zeroed. Offset: ", ACC.offset)

        elif topic == "time/fromground":
            if msg != "Disconnected":
                print('time received ', msg)
                HOIST.set_time(float(msg))
                client.unsubscribe('time/fromground')

        msg, topic = '', ''
        client.loop_stop()

finally:
    # opens relays broker keeps running but this file doesnt
    # and disconnect is ungraceful
    client.loop_stop()
    client.disconnect()
    HOIST.stop()
