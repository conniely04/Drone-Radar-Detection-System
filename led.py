import serial
import json
from gpiozero import LED
from time import sleep

# Setup LEDs (Pins 17, 27, 22)
red = LED(17)
yellow = LED(27)
green = LED(22)
leds = [red, yellow, green]

# Setup Serial Communication
# Usually /dev/ttyACM0 for USB radar sensors on Pi
SERIAL_PORT = '/dev/ttyACM0' 
BAUD_RATE = 115200

def update_leds(distance):
    # Reset
    for led in leds:
        led.off()

    # Threshold Logic 
    if distance <= 25.0:
        yellow.on()   # Caution Zone
    if distance <= 10.0:
        red.on()      # Danger/Stop Zone
    else: 
        green.on()    # Nothing is detected
    
    print(f"Current Distance: {distance}")

# Main Execution
try:
    # Initialize Serial connection
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"From Radar Sensor on {SERIAL_PORT}...")

    while True:
        if ser.in_waiting > 0:
            # Read a line of data from the sensor
            line = ser.readline().decode('utf-8').strip()
            
            try:
                # Parse JSON data (Standard OPS242 format)
                data = json.loads(line)
                
                # Extract distance 
                if 'dist' in data:
                    current_dist = float(data['dist'])
                    update_leds(current_dist)
                    
            except (json.JSONDecodeError, ValueError):
                # Skip lines that aren't valid JSON (like startup headers)
                continue

except KeyboardInterrupt:
    print("\nStopping...")
finally:
    for led in leds: led.off()
    if 'ser' in locals(): ser.close()
