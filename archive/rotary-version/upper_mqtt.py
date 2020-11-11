'''
Upper Pi MQTT Client

Runs two hoists, publishes and collects accelerometer, time, and height data.
This version uses a rotary encoder to measure height.
'''

import RPi.GPIO as GPIO
import time
import paho.mqtt.client as paho
import subprocess
import mpu6050
import hoist_control as HOIST
import timer
import rotary

''' Setup & Global Variables '''

angle_error_count = 0   # Sends accel disconnected once this hits certain num
ACC = mpu6050.ACC(offset=0)
ignore_angle = False    # Toggled by UI

ROTARY = rotary.Rotary(0.1)     # rotary encoder
last_msg_timer = timer.Timer()  # keeps time since last msg received

'''
MQTT Setup
'''
broker = "192.168.1.226"    # Config'd to be static
port = 9001                 # Set in mosquitto.conf
topic, msg = '', ''

def on_connect(client, userdata, flags, rc):
    global angle_thread, gndtime_thread, acc_err_thread, height_thread
    global ignore_angle

    client.subscribe("hoist")
    client.subscribe("time/fromground")
    client.subscribe("accelerometer/status")
    client.subscribe("height/status")
    print("connected")

    client.publish("status", "Upper Pi client connected")
    gndtime_thread = timer.setInterval(5, publish_gndtime)
    gndtime_thread.start()
    height_thread = timer.setInterval(.5, publish_height)
    height_thread.start()
    acc_err_thread = timer.setInterval(.5, accel_disconnect)

    if ACC.error == True:
        ignore_angle = True
        acc_err_thread.start()
    else:
        angle_thread = timer.setInterval(0.25, publish_angle)
        angle_thread.start()

def on_message(client, userdata, message):
    global topic, msg, last_msg_timer
    topic = message.topic
    msg = message.payload.decode("utf-8")

    # Starts counting time since msg received
    last_msg_timer.start()

def on_disconnect(client, userdata, rc):
    global angle_thread, gndtime_thread, height_thread
    global broker, port

    # Stops hoist and stops publishing angle
    HOIST.stop()
    try:
        angle_thread.cancel()
        gndtime_thread.cancel()
        height_thread.cancel()
    except NameError:
        pass
    print("client disconnected. Reason code", rc)

    # Attempts to reconnect to broker (self)
    time.sleep(3)
    client.connect(broker, port, keepalive=5)

'''
Processing and publishing data
'''

angle_lst = [0,1,2,3,4,5]  # keeps track of prev angles
angle_i = 0         # counter for index of angle_lsg

def publish_angle():
    global angle_thread, angle_lst, angle_i, angle_error_count

    # Deals with error of angle being stuck & published but no IOError
    if ACC.error == False:

        if (angle_i == 6):
            angle_i = 0

        angle = ACC.angle()
        angle_lst[angle_i] = angle
        angle_i += 1

        # 6 errors every 0.25s = 1.5s of errors
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

    # This to reattempt taking + publishing angle for 2 sec before
    # reporting disconnect to UI
    if recourse == "retry":
        angle_error_count += 1

        # Stops publishing accel data if disconnected for over 2sec
        if angle_error_count == 8:
            HOIST.stop()
            try:
                angle_thread.cancel()
            except:
                pass
            print("accelerometer disconnect - 2s")
            client.publish("accelerometer/status", "Disconnected")

    # Immediately reports accel disconnected to UI
    else:
        print("accel disconnect immediate")
        client.publish("accelerometer/status", "Disconnected")

def all_same(lst):
    return not lst or lst.count(lst[0]) == len(lst)

def publish_gndtime():
    client.publish('time/fromground', str(HOIST.time_from_ground.curr))

def publish_height():
    client.publish('height', ROTARY.dist)


'''
Creates MQTT client & runs client loop
'''

clientID = "upper" + str(time.time())
client = paho.Client(clientID, transport='websockets')
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

client.will_set("status", "Upper Pi client disconnected", retain=False)
client.connect(broker, port, keepalive=3)

try:
    while True:

        client.loop_start()

        if (last_msg_timer.countup() >= 1):
            # timer starts in on_message received
            HOIST.stop()

        # Topic in charge of hoist controls
        elif topic == "hoist":
            print(msg)

            if msg == "Off":
                HOIST.stop()

            elif msg == "Switch to backup":
                client.unsubscribe("hoist")

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

        # For accel communciation that is not the angle
        elif topic == "accelerometer/status":

            if msg == "Zero accelerometer":
                ACC.offset = ACC.angle_raw()
                HOIST.set_offset(ACC.offset)
                print("Accelerometer zeroed. Offset: ", ACC.offset)

        # For sending time from ground
        elif topic == "time/fromground":
            print('time received ', msg)
            try:
                HOIST.set_time(float(msg))
            except:
                print('error in time from ground: ', msg)
                pass

        # For zeroing the height
        elif topic == "height/status":
            if msg == 'Zero height':
                ROTARY.zero_height()
                print('Height zeroed')

        msg, topic = '', ''
        client.loop_stop()

# This happens if broker keeps running but something in the while
# loop crashes or client disconnect is ungraceful
finally:
    HOIST.stop()
    GPIO.cleanup()
    client.disconnect()
