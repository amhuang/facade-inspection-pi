# Facade Inspection Robot

The following is a description of the facade inspection robot software.

Requires I2C to be enabled. SSH and VNC are useful as well. Dependencies can be installed by running `setup.sh`. Wiring for the internals of the hoist control boxes and for all the sensors can be found in the Drive.

All communication utilizes MQTT with Websockets. The Pis should start up and connect to each other automatically on boot, but it might be helpful to have an IP address scanner (e.g. Angry IP Scanner) to obtain each Pi's IP address. The addresses are set to be static on each Pi and are already saved in the UI, so this should only be necessary once if at all. The IP addresses can also be used to interface with the Pis via SSH or VNC, and are also necessary for the UI to connect to the system.

### Upper Pi

This Pi should be configured to automatically run `upper.sh` on startup.

What this Pi does:

- Given commands from the UI, this can level the frame in place, run the two hoists together with or without a leveling algorithm, and run each hoist independently.
- Hosts an MQTT broker (port: 9001) to which all Pis and the UI are connected
- Publishes pitch (angle of frame) from accelerometer via MQTT to the broker
- Upon losing connection with its accelerometer, it will either a) transfer hoist control and accelerometer data publishing capabilities to the backup Pi, or b) continue to operate both hoists without leveling. The operator can choose one of these two options from the GUI.
- Publishes the frame's time from ground to the UI. Receives time from ground from the UI if upper Pi client gets disconnected and reconnects.
- Streams input from three USB cameras to the GUI via mjpg-streamer (port: 8080)

What this Pi is connected to:

- Accelerometer
- Rotary encoder
- Both hoists
- 3 USB cameras
- Ethernet to router

### Lower Pi

This Pi should be configured to automatically run `lower.sh` on startup.

What this Pi does:

- Streams input from three USB cameras via mjpg-streamer (port: 8080)

- Stays subscribed to the MQTT broker on the upper Pi at all times.

- Receives and stores the frame's time from ground from the upper Pi client.

- Does NOT take height

- Acts as a backup if the upper Pi disconnects from its accelerometer and the operator chooses to switch to the backup Pi to operate. Upon receiving the "Switch to backup" message on the topic "hoist", this Pi does two things:
  1. It enables listens and executes up/down commands from the UI instead of the upper Pi, and
  2. Publishes pitch from accelerometer to the UI

- Acts as a backup in the case of upper Pi losing power. Upon disconnecting from the MQTT broker, this Pi does the following:
  1. Runs the script that starts another MQTT broker on this Pi (port: 9001). The UI and lower Pi try to connect to this when they disconnect from the original broker (upper Pi).
  2. Gains control over hoists by subscribing to topic "hoist"
  3. Publishes pitch from accelerometer to the UI

 - Upon losing connection with its accelerometer, it will continue to operate both hoists without leveling.

What this Pi is connected to:

- Accelerometer
- 3 USB cameras
- Both hoists
- Ethernet to router
