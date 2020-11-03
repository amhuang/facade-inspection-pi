#!/bin/bash
cd /home/pi/facade-inspection-pi/mqttserver

(mosquitto -c /etc/mosquitto/mosquitto.conf) &

(sleep 1
python3 start_stream.py) &

(sleep 3
python3 upper_mqtt.py)

function finish
{
    sudo service mosquitto stop
    sudo killall mjpg_streamer mosquitto
    echo cleaned up
}
trap finish EXIT
