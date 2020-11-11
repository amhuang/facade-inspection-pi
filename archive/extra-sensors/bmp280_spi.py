import time
import board

import digitalio
# For use with SPI
import busio
import adafruit_bmp280

# create library object using our Bus SPI port
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
bmp_cs = digitalio.DigitalInOut(board.D5)
bmp280 = adafruit_bmp280.Adafruit_BMP280_SPI(spi, bmp_cs)

# change this to match the location's pressure (hPa) at sea level
bmp280.sea_level_pressure = 1015.8


def altitude():
    height = bmp280.altitude - height_0
    return height

def pressure():
    return bmp280.pressure

def temperature():
    celcius = bmp280.temperature
    fahr = (celcius * (9/5)) + 32
    return fahr

def print_readings():
    celcius = bmp280.temperature
    fahr = (celcius * (9/5)) + 32
    print("\nTemperature: %0.1f F" % fahr)
    print("Pressure: %0.1f hPa" % bmp280.pressure)
    print("Altitude = %0.2f meters" % bmp280.altitude)

def zero_height():
    global height_0
    height_0 = bmp280.altitude
