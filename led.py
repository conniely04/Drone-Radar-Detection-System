import serial
import json
import time
from gpiozero import LED

# --- CONFIGURATION ---
SERIAL_PORT = '/dev/ttyACM0' 
BAUD_RATE = 19200

# Range Thresholds in METERS
# Adjusted based on area
THRESH_RED    = 0.5   # Object is within 0.5m (Very Close)
THRESH_YELLOW = 1.5   # Object is within 1.5m (Caution)
THRESH_GREEN  = 3.0   # Object is within 3.0m (Detected)

# Initialize Hardware
red, yellow, green = LED(17), LED(27), LED(22)
leds = [red, yellow, green]

def update_physical_leds(range_m):
    # Reset all LEDs
    for led in leds:
        led.off()

    # Smaller meter value = closer proximity
    if range_m < THRESH_RED:
        red.on()
    elif range_m < THRESH_YELLOW:
        yellow.on()
    elif range_m < THRESH_GREEN:
        green.on()

def main():
    try:
        # Initialize Serial
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        
        # SENSOR INIT: Send API commands to ensure JSON + Magnitude
        ser.write(b'OJ\n')  # Enable JSON
        ser.write(b'OR\n')  # Enable Magnitude
        time.sleep(1)       # Give sensor a moment to process
        
        while True:
                    if ser.in_waiting > 0: # Checks for new data
                        raw_line = ser.readline().decode('utf-8', errors='ignore').strip() # Grabs line of data from sensor
                        
                        if '{' in raw_line and '}' in raw_line: # Ensures JSON format
                            try:
                                start = raw_line.find('{')
                                end = raw_line.rfind('}') + 1
                                data = json.loads(raw_line[start:end])  # JSON string to Python dictionary
                                
                                if "range" in data:
                                    range_val = float(data["range"])
                                update_physical_leds(range_val)
                        
                        except (json.JSONDecodeError, ValueError):
                            continue

    except Exception as e:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        for led in leds: led.off()
        if 'ser' in locals(): ser.close()

if __name__ == "__main__":
    main()
