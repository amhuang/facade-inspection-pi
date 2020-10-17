#!/bin/bash
cd /home/pi/facade-inspection-pi/mqttserver

(sleep 3
python3 start_stream.py) &

(sleep 10
python3 lower_mqtt.py)

function finish
{
    sudo service mosquitto stop
    sudo killall mjpg_streamer mosquitto
    echo cleaned up
}
trap finish EXIT
