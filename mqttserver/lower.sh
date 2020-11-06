#!/bin/bash
cd /home/pi/facade-inspection-pi/mqttserver

# Starts videos streams
(sleep 20
python3 start_stream.py) &

# Opens MQTT client which connects to broker on upper
(sleep 60
python3 lower_mqtt.py)

# Runs on ctrl-C to clean up everything
function finish
{
    sudo service mosquitto stop
    sudo killall mjpg_streamer mosquitto
    echo cleaned up
}
trap finish EXIT
