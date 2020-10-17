# Facade Inspection Robot

The following is a description of the components of the software for the facade inspection robot.

All communication utilizes MQTT with Websockets. You'll to know the IP addresses of the Pis' on the network you're using in order to interface with them via VNC/SSH, so it might be helpful to have an IP address scanner (for example, Angry IP Scanner). These addresses are also necessary for the GUI for connecting to the MQTT broker and viewing the livestreams.

The instructions for installing necessary dependencies on the Pis, wiring the internals of the hoist control boxes, as well as wiring for all the sensors can be found in the Drive.

### Upper Pi

This Pi should be configured to automatically run `exec_upper.sh` on startup.

What this Pi does:

- Given commands from the GUI, can run the two hoists together using a leveling algorithm or each one independently
- Runs an MQTT broker (port: 9001), to which all Pi's and the UI are connected
- Publishes pitch data from accelerometer via MQTT to the broker
- Upon losing connecting with its accelerometer will either a) transfer hoist control and accelerometer data publishing capabilities to the backup Pi, or b) continue to operate both hoists without leveling. The operator can choose one of these two options from the GUI.
- Streams input from three USB cameras via mjpg-streamer (port: 8080)

What this Pi is connected to:

- Accelerometer
- Both hoists
- 3 USB cameras

### Backup Pi

This Pi should be configured to automatically run `exec_backup.sh` on startup.

What this Pi does:

- Stays subscribed to the MQTT broker on the upper Pi at all times
- Acts as a backup if the upper Pi disconnects from its accelerometer and the operator chooses to switch to the backup Pi to operate. Upon receiving the "Switch to backup" message on the topic "hoist", this Pi does two things:
  1. It enables listens and executes up/down commands from the UI instead of the upper Pi, and
  2. Publishes accelerometer pitch data to the UI

- Acts as a backup in the case of upper Pi losing power. Upon disconnecting from the MQTT broker, this Pi does the following:
  1. Runs the script that starts another MQTT broker on this Pi (port: 9001). The UI and lower Pi try to connect to this when they disconnect from the original broker (upper Pi).
  2. Gains control over hoists by subscribing to topic "hoist"
  3. Publishes pitch from accelerometer to the UI

What this Pi is connected to:

- Accelerometer
- Both hoists

### Lower Pi

This Pi should be configured to automatically run `exec_lower.sh` on startup.

What this Pi does:

- Publishes data from altimeter to the MQTT broker (UpperPi) on topic "altimeter/altitude", "altimeter/temperature", and "altimeter/pressure"
- Receives current sea level pressure input from UI on topic "altimeter/sealevelpressure"
- Upon disconnecting from its broker (upper Pi), reconnects to the broker on the backup Pi
- Streams input from three USB cameras via mjpg-streamer (port: 8080)

What this Pi is connected to:

- Altimeter (via I2C)
- 3 USB cameras
