#!/bin/bash
cd /home/pi/facade-inspection-pi/mqttserver

# Starts video streams then starts MQTT broker
(sleep 20s
python3 start_stream.py
) &

# Opens MQTT client which connects to brokers
# Time is long bc router takes forever to turn on but honestly I'm not
# really sure so maybe think abt this
(sleep 55s
mosquitto -c /etc/mosquitto/mosquitto.conf) &

(sleep 60s
python3 upper_mqtt.py)

# Runs on ctrl-C to clean up everything
function finish
{
    sudo service mosquitto stop
    sudo killall mjpg_streamer mosquitto
    echo cleaned up
}
trap finish EXIT
