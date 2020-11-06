#!/bin/bash
cd /home/pi/facade-inspection-pi/mqttserver

# Starts video streams then starts MQTT broker
(sleep 20
python3 start_stream.py
mosquitto -c /etc/mosquitto/mosquitto.conf) &

# Opens MQTT client which connects to brokers
# Time is long bc router takes forever to turn on but honestly I'm not
# really sure so maybe think abt this
(sleep 50
python3 upper_mqtt.py)

# Runs on ctrl-C to clean up everything
function finish
{
    sudo service mosquitto stop
    sudo killall mjpg_streamer mosquitto
    echo cleaned up
}
trap finish EXIT
