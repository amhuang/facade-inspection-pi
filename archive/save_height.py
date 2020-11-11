# This takes the average height every second and
# saves time vs height data to a file

import altimeter
import time
from datetime import datetime
import csv

start_time = time.time()

now_time = time.time()
time_passed = now_time - start_time

date_time = str(datetime.now())

folder_dir = "~/facade-inspection-pi/data"
fields = ['Time (s)', 'Height (m)']
file_dir = folder_dir + date_time + ".csv"

data_file = open(file_dir, 'w')
csvwriter = csv.writer(data_file)
csvwriter.writerow(fields)

while True:
    height_average = []

    while time_passed < 1.00:
        height_average.append(altimeter.altitude())
        now_time = time.time()
        time_passed = now_time - start_time

    height = sum(height_average)/len(height_average)

    data_file = open(file_dir + date_time + ".txt", 'a')

    csvwriter.writerow(time_passed)
