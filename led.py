import serial
import json
import time
from gpiozero import LED

# --- CONFIGURATION ---
SERIAL_PORT = '/dev/ttyACM0' 
BAUD_RATE = 19200

# Magnitude Thresholds (Adjust once the sensor is in the enclosure)
THRESH_RED = 800.0
THRESH_YELLOW = 350.0
THRESH_GREEN = 50.0

# Initialize Hardware
red, yellow, green = LED(17), LED(27), LED(22)
leds = [red, yellow, green]

def update_physical_leds(magnitude):
    # Updates LED states based on magnitude
    # Turning all off to ensure clean state
    for led in leds:
        led.off()

    if magnitude > THRESH_RED:
        red.on()
        return "DANGER: Object Close"
    elif magnitude > THRESH_YELLOW:
        yellow.on()
        return "WARNING: Object Nearby"
    elif magnitude > THRESH_GREEN:
        green.on()
        return "DETECTED: Object Far"
    else:
        return "CLEAR"

def main():
    try:
        # Initialize Serial
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        
        # SENSOR INIT: Send API commands to ensure JSON + Magnitude
        ser.write(b'OJ\n')  # Enable JSON
        ser.write(b'OM\n')  # Enable Magnitude
        time.sleep(1)       # Give sensor a moment to process
        
        while True:
                    if ser.in_waiting > 0: # Checks for new data
                        raw_line = ser.readline().decode('utf-8', errors='ignore').strip() # Grabs line of data from sensor
                        
                        if '{' in raw_line and '}' in raw_line: # Ensures JSON format
                            try:
                                start = raw_line.find('{')
                                end = raw_line.rfind('}') + 1
                                data = json.loads(raw_line[start:end])  # JSON string to Python dictionary
                                
                                mag = float(data.get("magnitude", 0))   # Collects magnitude data
                                status = update_physical_leds(mag)      # Updates LED indicator based on mag value
                                
                                # Only prints the essential status line
                                print(f"Mag: {mag:7.2f} | Status: {status}")
                                
                            except (json.JSONDecodeError, ValueError):  # Data Filter, in case of "bad" data
                                continue

    except Exception as e:
        print(f"System Error: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        for led in leds: led.off()
        if 'ser' in locals(): ser.close()

if __name__ == "__main__":
    main()
