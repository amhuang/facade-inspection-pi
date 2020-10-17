#!/bin/bash
cd /home/pi/facade-inspection-pi/mqttserver

sleep 10
python3 backup_mqtt.py

function finish
{
    sudo service mosquitto stop
    sudo killall mosquitto
    echo cleaned up
}
trap finish EXIT
