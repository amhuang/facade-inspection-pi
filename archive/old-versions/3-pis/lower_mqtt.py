''' For LowerPi
'''
import RPi.GPIO as GPIO
import time
import paho.mqtt.client as paho
import mpl3115a2 as ALT
import subprocess
import timer

''' Motor Setup '''

broker = "192.168.1.235"    # IP of MAIN broker Pi
backupBroker = "192.168.1.113"
port = 9001                 # Set in mosquitto.conf

''' MQTT Setup '''

def on_connect(client, userdata, flags, rc):
    global altitude_thread
    client.subscribe("altimeter/sealevelpressure")
    altitude_thread = timer.setInterval(1.0, publish_all_alti)
    altitude_thread.start()
    print("connected")

def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed")

def on_message(client, userdata, message):
    msg = message.payload.decode("utf-8")
    print(msg)
    if message.topic == "altimeter/sealevelpressure":
        ALT.sealevel_pressure(float(msg))

    # Not listening to anything bc the only time you would have to do switch
    # brokers is on disconnect

def on_disconnect(client, userdata, rc):
    global altitude_thread
    print("Lower Pi client disconnected")
    altitude_thread.cancel()

    # Connects to new broker on backup when main loses power
    broker = backupBroker
    client.connect(broker,port,keepalive=5)
    client.loop_forever()

def publish_all_alti():
    try:
        alt = ALT.altitude()
        client.publish("altimeter/altitude", alt)

        temp = "%.1f" % ALT.temperature()
        client.publish("altimeter/temperature", temp)

        press = "%.2f" % ALT.pressure()
        client.publish("altimeter/pressure", press)

    except:
        altitude_thread.cancel()
        client.publish("altimeter/altitude", "Disconnected")
        client.publish("altimeter/temperature", "Disconnected")
        client.publish("altimeter/pressure", "Disconnected")

# Instantiates new client. Make sure the name is diff from others
clientID = "lower" + str(time.time())
client = paho.Client(clientID, transport='websockets')

# Callback functions for client set when .loop_start() called
client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_disconnect = on_disconnect

# Subscribes to "hoist" first time connected
client.connect(broker, port, keepalive=5)
client.loop_forever()
