# Object Detection Dashboard

A React-based dashboard for real-time object detection monitoring using a Raspberry Pi infrared camera.

## Features

### Frontend Dashboard Components:
1. **Camera Feed Display**
   - MJPEG library integration for real-time camera streaming
   - Placeholder component for Raspberry Pi infrared camera
   - Connection controls with URL input
   - Live/disconnected status indicator

2. **Object Detection Log**
   - Real-time display of detected objects
   - Speed measurement in mph
   - Distance measurement in feet
   - Timestamp logging
   - Object type and confidence level display
   - History table with recent detections

### Current Implementation:
- Built with React + Vite
- Responsive design with CSS Grid
- Mock data simulation for development
- Clean, modern UI with gradient backgrounds
- Mobile-friendly responsive layout

## Getting Started

### Prerequisites
- Node.js (v18 or higher)
- npm

### Installation
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and go to `http://localhost:5173` (or the port shown in terminal)

## Project Structure
```
198seniorproj/
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── CameraFeed.jsx          # Camera display component
│   │   │   ├── CameraFeed.css          # Camera styling
│   │   │   ├── ObjectDetectionLog.jsx  # Detection log component
│   │   │   └── ObjectDetectionLog.css  # Log styling
│   │   ├── Dashboard.jsx               # Main dashboard layout
│   │   ├── Dashboard.css               # Dashboard styling
│   │   ├── App.jsx                     # App entry point
│   │   ├── App.css                     # App styling
│   │   └── index.css                   # Global styles
│   └── package.json
└── backend/                    # Python Flask backend (ready for Pi)
    ├── app.py                  # Main Flask application (for Pi)
    ├── app_dev.py              # Development mock backend
    ├── camera_system.py        # Camera handling module
    ├── radar_sensor.py         # Sensor communication module
    ├── config.py               # Configuration settings
    ├── requirements.txt        # Pi dependencies
    ├── requirements_dev.txt    # Development dependencies
    └── setup.sh                # Pi setup script
```

## Current Status
- **Frontend**: ✅ Fully functional with mock data
- **Backend**: ✅ Code ready for Raspberry Pi deployment
- **Integration**: 🚧 Ready for future backend connection

## Future Integration Plans

### Backend Integration (Raspberry Pi):
- Raspberry Pi OS (Bookworm), 64-bit
- Flask server for camera streaming
- UART communication with radar sensor
- pyserial library for data processing
- Real camera feed via MJPEG stream

### Camera Setup:
- Replace placeholder with actual Raspberry Pi camera URL
- Configure infrared camera settings
- Implement proper error handling for camera disconnections

### Data Processing:
- Replace mock data with real radar sensor data
- Implement data validation and filtering
- Add data persistence and logging

## Technology Stack
- **Frontend**: React 18, Vite
- **Styling**: Plain CSS with modern features
- **Future Backend**: Python Flask, Raspberry Pi
- **Camera**: MJPEG streaming protocol

## Development Notes
- Frontend uses mock data for development (no backend connection needed)
- Backend code is ready for Raspberry Pi deployment
- Camera feed shows placeholder until real camera is connected
- "Simulate Detection" button generates random test data
- Responsive design works on desktop and mobile devices
- Real-time mock updates every 10 seconds

## Next Steps
1. Set up Raspberry Pi backend
2. Configure infrared camera
3. Implement radar sensor integration
4. Connect real data streams
5. Add data persistence
6. Implement user authentication (if needed)