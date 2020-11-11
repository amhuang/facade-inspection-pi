''' This should always be run on the backup Pi when it starts up. The
backup Pi starts out connected to broker and subscribed to the "hoist" topic.

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
import mpu6050 as ACC
import subprocess
import setInterval as thread
import threading

''' Motor Setup '''

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

UP_L, DOWN_L = 19, 26
UP_R, DOWN_R = 20, 21

GPIO.setup(UP_L,GPIO.OUT)
GPIO.setup(DOWN_L,GPIO.OUT)
GPIO.setup(UP_R,GPIO.OUT)
GPIO.setup(DOWN_R,GPIO.OUT)

broker = "192.168.1.235"    # IP of MAIN broker Pi
backupBroker = "192.168.1.113"
port = 9001                 # Set in mosquitto.conf

backup_listen = False
ignore_angle = False
msg, topic = '', ''

''' MQTT Setup '''

def on_connect(client, userdata, flags, rc):
    client.subscribe('status')
    print("connected")

def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed")

def on_message(client, userdata, message):
    global backup_listen, msg, topic
    msg = message.payload.decode("utf-8")
    topic = message.topic

    # Deals with Scenario 2 - original broker stays on
    if msg == "Switch to backup" or msg == 'Upper Pi client disconnected':
        backup_listen = True
        thread.setInterval(0.2, publish_angle)

def on_disconnect(client, userdata, rc):
    print("I'm disconnected")

    # Starts a new broker on backup when main loses power
    run_broker = subprocess.Popen(["sh", "mqttBroker.sh"])
    time.sleep(0.5)
    thread.setInterval(0.2, publish_angle)
    backup_listen = True
    broker = backupBroker

    client.connect(broker,port)
    client.subscribe("hoist")
    client.loop_start()

# Instantiates new client. Make sure the name is diff from others
client = paho.Client("lowerPi",transport='websockets')

# Callback functions for client set when .loop_start() called
client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_disconnect = on_disconnect

# Subscribes to "hoist" first time connected
client.connect(broker, port, keepalive=3)
client.subscribe("hoist")
client.subscribe("status")
client.loop_start()


''' Functions to publish data to broker '''

def publish_angle():
    angle = "%.1f" % ACC.angleRaw()
    client.publish("accelerometer/angle", angle)

try:
    while True:
        client.loop_start()

        # Enters with either Scenario 1 or 2
        if backup_listen:
            if (last_msg_timer.countup() >= 1 or HOIST.time_from_ground.curr <= -5):
                # timer starts in on_message received
                HOIST.stop()

            elif topic == "hoist":
                #exec_shutdown.start()
                print(msg)

                if msg == "Off":
                    HOIST.stop()

                elif msg == "Switch to backup":
                    client.unsubscribe("hoist")

                elif msg == "Make level":
                    HOIST.make_level()

                elif msg == "Toggle leveling":
                    if ignore_angle:
                        ignore_angle = False
                    else:
                        ignore_angle = True

                else:
                    if msg == "Up":
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

                if msg == "Ignore angle":
                    HOIST.ignore_angle = True

                elif msg == "Stop ignoring angle":
                    HOIST.ignore_angle = False

                elif msg == "Zero accelerometer":
                    ACC.offset = ACC.angle_raw()
                    HOIST.set_offset(ACC.offset)
                    print("Accelerometer zeroed. Offset: ", ACC.offset)

            elif topic == "time/fromground":
                print('time received ', msg)
                HOIST.set_time(float(msg))
                client.unsubscribe('time/fromground')

            msg, topic = '', ''
            client.loop_stop()

finally:
    # opens relays broker keeps running but this file doesnt
    # and disconnect is ungraceful
    HOIST.stop()
