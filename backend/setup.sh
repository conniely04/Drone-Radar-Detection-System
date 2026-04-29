#!/bin/bash

# Object Detection System Backend Setup Script
# For Raspberry Pi OS (Bookworm)

echo "🚀 Setting up Object Detection Backend on Raspberry Pi..."

BACKEND_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BACKEND_DIR" || exit 1

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
sudo apt install -y python3-pip python3-venv python3-dev

# Install frontend runtime
echo "🌐 Installing Node.js and npm for the React frontend..."
sudo apt install -y nodejs npm

# Install system dependencies for OpenCV
echo "📷 Installing OpenCV system dependencies..."
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y libatlas-base-dev libhdf5-dev libhdf5-serial-dev
sudo apt install -y libqtgui4 libqt4-test

# Install Pi-friendly PyTorch packages for YOLO inference.
echo "🧠 Installing PyTorch for computer vision..."
sudo apt install -y python3-torch python3-torchvision

# Install camera dependencies (for Pi Camera)
echo "📹 Installing camera dependencies..."
sudo apt install -y python3-picamera2

# Install serial communication tools
echo "🔌 Installing serial communication tools..."
sudo apt install -y python3-serial

# Create virtual environment
echo "🔧 Creating Python virtual environment..."
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# Install Python packages
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
pip install ultralytics --no-deps

# Enable camera interface
echo "📷 Enabling camera interface..."
sudo raspi-config nonint do_camera 0

# Enable serial interface (for UART communication)
echo "🔌 Enabling serial interface..."
sudo raspi-config nonint do_serial 0

# Create systemd service for auto-start (optional)
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/object-detection.service > /dev/null <<EOF
[Unit]
Description=Object Detection Backend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$BACKEND_DIR
Environment=PATH=$BACKEND_DIR/.venv/bin
ExecStart=$BACKEND_DIR/.venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chmod +x setup.sh

echo "✅ Setup complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. Activate virtual environment: source .venv/bin/activate"
echo "3. Run the backend: python app.py"
echo "4. Or enable auto-start: sudo systemctl enable object-detection.service"
echo ""
echo "🌐 The backend will be available at: http://your-pi-ip:5001"
echo "📷 Camera stream at: http://your-pi-ip:5001/api/camera/stream"
