'''
Backup Pi MQTT Client

This script is equipped to handle 2 scenarios:
1. Power to main Pi (broker) lost. On disconnection from the broker, it will
    run a one-line command to start up a new broker on this Pi running in the
    background while running a backupMqttActive.py which is essentially
    identical to the hoist operation file on the original broker.
2. The accelerometer to the main Pi is disconnected. If selected as an option,
    the main Pi will send the message "Switch to backup" to the "hoist"
    topic, which will cause the main Pi to unsubscribe to "hoist" and thus not
    respond to messages from it. Upon receiving that message, this Pi will
    then be able to respond to "up" "off" and "down" from "hoist". The main Pi
    *will remain the broker* to avoid having to reconnect everything.
'''
import RPi.GPIO as GPIO
import time
import paho.mqtt.client as paho
import subprocess
import timer
import hoist_control as HOIST
import mpu6050

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
exec_shutdown = timer.Timer()

backup_listen = False

'''
MQTT Setup
'''

broker = "192.168.1.235"    # IP of MAIN broker Pi
backupBroker = "192.168.1.113"
port = 9001                 # Set in mosquitto.conf
msg, topic = '', ''

def on_connect(client, userdata, flags, rc):
    global backup_listen, angle_thread, acc_err_thread, timefromground_thread 
    client.subscribe("hoist")
    client.subscribe("status")
    client.subscribe("time/fromground")
    print("connected")
    
def on_message(client, userdata, message):
    global backup_listen, msg, topic
    global angle_thread, acc_err_thread, timefromground_thread 
    msg = message.payload.decode("utf-8")
    topic = message.topic
    last_msg_timer.start()

    # Deals with Scenario 2 - original broker stays on
    if msg == "Switch to backup" or msg == 'Upper Pi client disconnected':
        global backup_listen
        backup_listen = True
        
        # Try to start publishing angle
        if ACC.error == True:
            ignore_angle = True
            acc_err_thread = timer.setInterval(.5, accel_disconnect)
            acc_err_thread.start()
        else:
            angle_thread = timer.setInterval(0.25, publish_angle)
            angle_thread.start()
        
        # Starts publishing time from ground
        client.unsubscribe('time/fromground')
        timefromground_thread = timer.setInterval(5, publish_timefromground)
        timefromground_thread.start()
        
        client.publish("status", "Backup Pi client connected");
    
    # Keeps track of time from ground at all times
    elif topic == "time/fromground":
        if msg != 'Disconnected':
            print('time received ', msg)
            HOIST.set_time(float(msg))

def on_disconnect(client, userdata, rc):
    global broker
    print("Disconnected from broker")
    client.loop_stop()

    # Starts a new broker on backup when main loses power
    run_broker = subprocess.Popen(["mosquitto", "-c", "/etc/mosquitto/mosquitto.conf"])
    time.sleep(1)

    backup_listen = True
    broker = backupBroker

    client.connect(broker, port)
    client.subscribe("hoist")
    client.subscribe("status")
    client.subscribe("time/fromground")
    client.subscribe("accelerometer/status")
    
    try:
        timefromground_thread.cancel()
    except:
        pass
    timefromground_thread = timer.setInterval(5, publish_timefromground)
    timefromground_thread.start()
    
    if ACC.error == True:
        ignore_angle = True
        try:
            angle_thread.cancel()
        except:
            pass
        acc_err_thread = timer.setInterval(.5, accel_disconnect)
        acc_err_thread.start()
    else:
        angle_thread = timer.setInterval(0.25, publish_angle)
        angle_thread.start()

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
            client.publish("accelerometer/status", "Backup disconnected")
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
            try:
                angle_thread.cancel()
            except:
                pass
            print("accelerometer disconnect 1s")
            client.publish("accelerometer/status", "Backup disconnected")
    
    else:
        client.publish("accelerometer/status", "Backup disconnected")

def all_same(lst):
    return not lst or lst.count(lst[0]) == len(lst)

def publish_timefromground():
    client.publish('time/fromground', str(HOIST.time_from_ground.curr))

'''
Creates MQTT client & runs client loop
'''

# Instantiates new client. Make sure the name is diff from others
clientID = "backup" + str(time.time())
client = paho.Client(clientID, transport='websockets')

# Callback functions for client set when .loop_start() called
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.will_set("status", "Backup Pi client disconnectetd", retain=False)

# Subscribes to "hoist" first time connected

client.connect(broker, port, keepalive=5)

try:
    while True:
        client.loop_start()

        # Enters with either Scenario 1 or 2
        if backup_listen:

            if (last_msg_timer.countup() >= 1 or HOIST.time_from_ground.curr <= -5):
                # timer starts in on_message received
                HOIST.stop()

            elif topic == "hoist":
                print(msg)
                
                if msg == "Off":
                    HOIST.stop()

                elif msg == "Disable leveling":
                    ignore_angle = True
                    try:
                        acc_err_thread.cancel()
                        print("cancel thread")
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

            msg, topic = '', ''
        client.loop_stop()

finally:
    # opens relays broker keeps running but this file doesnt
    # and disconnect is ungraceful
    HOIST.stop()
