# Serial Port Reading Setup Guide

## Overview

Your system now has integrated serial port reading without requiring the `screen` command. The backend directly reads from the serial port and streams the data to your frontend dashboard.

## How It Works

### Backend (`app.py`)

- **`/api/system/available-ports`** - Get list of all available serial ports
- **`/api/system/port-info`** (POST) - Connect to a specific serial port
- **`/api/sensor/raw`** - Get last raw sensor readings
- **`/api/sensor/stream`** - Server-Sent Events stream for real-time data

### Frontend (`Dashboard.jsx`)

- Serial port selector dropdown with auto-detection
- Real-time display of raw sensor data from the selected port
- Live updates as new data arrives from the serial port

## Usage Steps

### 1. Start the Backend

```bash
cd /Users/conniely/198seniorproj/backend
python3 app.py
```

### 2. Start the Frontend

```bash
cd /Users/conniely/198seniorproj/frontend
npm run dev
```

### 3. Select and Connect to Serial Port

1. Open the dashboard in your browser (`http://localhost:5173` or whatever Vite shows)
2. Look for the "Serial Port Configuration" section in the header
3. Click "Refresh Ports" to populate the dropdown
4. Select your port (e.g., `/dev/cu.usbmodem11101`)
5. Click "Connect"

### 4. View Real-Time Data

- Raw sensor data will appear in the "Raw Sensor Data" section
- Each line shows the timestamp and exact data from your serial device
- Data is kept in a rolling buffer of the last 50 readings

## API Examples

### Get Available Ports

```bash
curl http://localhost:5001/api/system/available-ports
```

Response:

```json
{
  "ports": [
    {
      "device": "/dev/cu.usbmodem11101",
      "description": "USB Modem",
      "manufacturer": "Silicon Labs"
    }
  ]
}
```

### Connect to a Port

```bash
curl -X POST http://localhost:5001/api/system/port-info \
  -H "Content-Type: application/json" \
  -d '{"port": "/dev/cu.usbmodem11101"}'
```

### Get Raw Sensor Data

```bash
curl http://localhost:5001/api/sensor/raw
```

Response:

```json
{
  "raw_data": [
    {
      "timestamp": "2026-02-25T01:30:00.123456",
      "raw_data": "SPEED:45.2,DISTANCE:30.5,CONFIDENCE:0.95"
    }
  ],
  "count": 1,
  "latest": {
    "timestamp": "2026-02-25T01:30:00.123456",
    "raw_data": "SPEED:45.2,DISTANCE:30.5,CONFIDENCE:0.95"
  }
}
```

## Troubleshooting

### No ports appear in dropdown

1. Check the port is properly connected: `ls /dev/cu.*`
2. Click "Refresh Ports" again
3. Check permissions on the port: `ls -la /dev/cu.usbmodem*`

### Connection fails

1. Make sure the port is not in use by other applications
2. Kill any existing connections: `lsof -ti /dev/cu.usbmodem11101 | xargs kill -9`
3. Try selecting and connecting again

### Not seeing new data

1. Check that your serial device is actually sending data
2. Verify the port is connected (status should show "✅ Connected to: /dev/cu.usbmodem11101")
3. Check browser console for any JavaScript errors

## Data Format

The system stores raw serial data as-is. If your sensor sends:

```
SPEED:45,DISTANCE:30,CONFIDENCE:0.95
```

The system will display and parse it exactly as received. To modify parsing logic, edit the `parse_sensor_data()` method in `app.py`.

## Important Notes

- The system keeps the last **100 detection records** and **1000 raw serial readings** in memory
- Data is not persisted; it clears when the backend restarts
- Raw data is displayed for **debugging purposes** - parsed detection data is used for analysis
- The frontend updates in real-time with Server-Sent Events (no polling)
