#!/bin/bash

# Installs and configures dependencies necessary for a blank Pi
cat requirements.txt | xargs sudo apt-get install
sudo pip3 install paho-mqtt adafruit-circuitpython-mpl3115a2s

# Install mjpg-streamer
cd
git clone https://github.com/jacksonliam/mjpg-streamer.git
cd mjpg-streamer/mjpg-streamer-experimental
make
sudo make install

# Install MQTT with websockets
cd
wget http://mosquitto.org/files/source/mosquitto-1.6.12.tar.gz
tar zxvf mosquitto-1.6.12.tar.gz
cd mosquitto-1.6.12
sudo sed -i 's/WITH_WEBSOCKETS:=no/WITH_WEBSOCKETS:=yes/' config.mk
make
sudo make install
sudo cp mosquitto.conf /etc/mosquitto
sudo sed -i 's/default listener\./default listener\.\nlistener 9001\nprotocol websockets/' /etc/mosquitto/mosquitto.conf
#sudo adduser mosquitto

# Set up I2C
sudo sed -i 's/i2c-dev/i2c-dev\ni2c-bcm2708/' /etc/modules

# Write this .desktop file to have everything start on startup properly
# sudo nano /etc/xdg/autostart/custom.desktop
# [Desktop Entry]
# Exec=lxterminal --command="/bin/bash -c '/home/pi/facade-inspection-pi/mqttservttserver/exec_WHICHPI.sh; /bin/bash'"
