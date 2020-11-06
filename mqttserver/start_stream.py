'''
Regex to grab v4l2 ID off each camera  (/dev/videoX) from cmd line args
and uses them to start mjpg-steramer to port 8080
'''

import subprocess
import re
import time

v4l2_dev = subprocess.Popen(['v4l2-ctl', '--list-devices'], stdout=subprocess.PIPE)
dev_info = str(v4l2_dev.stdout.read())

pattern = re.compile(r'(?<=\(usb-0000:01:00.0-1.[1-4]\):\\n\\t)/dev/video.')
devices = re.findall(pattern, dev_info)

port = 8080
lst = ["mjpg_streamer"]

for device in devices:
    lst.append("-i")
    lst.append("input_uvc.so -d " + device + " -r 1920x1080")

lst.append("-o")
lst.append("output_http.so -p " + str(port))
subprocess.Popen(lst)
