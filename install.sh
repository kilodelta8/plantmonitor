#!/bin/bash

# **********************************************************************
# @file   install.sh
# @author John Durham
# @date   10/27/2025
# @brief  This script installs the necessary dependencies for the project
#         and sets up the environment for the "PlantMonitor" application.
# **********************************************************************

# This script performs the following tasks on the Raspberry Pi:
# 1. Installs necessary Python dependencies (Flask, pyserial, requests).
# 2. Creates the project directory structure.
# 3. Copies the application files (app.py, templates/index.html).
# 4. Finds the Python 3 executable path.
# 5. Creates or updates the systemd service unit file (plant_waterer.service)
#    with the provided API Key and City Name.
# 6. Enables and starts the systemd service to run the app on boot.
# 7. Provides an interactive diagnostic tool for connecting the Arduino.

# --- CONFIGURATION ---
PROJECT_DIR="/home/pi/plant-waterer"
SERVICE_NAME="plant_waterer.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
PYTHON_DEPS="Flask pyserial requests"

# --- 1. ARGUMENT CHECK ---
if [ "$#" -ne 2 ]; then
    echo "Usage: sudo ./install.sh [YOUR_OPENWEATHERMAP_API_KEY] \"[CITY NAME]\""
    echo "Example: sudo ./install.sh 12345abcdef \"San Diego\""
    exit 1
fi

API_KEY="$1"
CITY_NAME="$2"

echo "--------------------------------------------------------"
echo "  Star Track Plant Waterer: Automated Installation"
echo "--------------------------------------------------------"
echo "Project Directory: $PROJECT_DIR"
echo "City Name: $CITY_NAME"
echo ""

# --- 2. DEPENDENCY INSTALLATION ---
install_dependencies() {
    echo "Checking and installing Python dependencies..."
    
    # Use 'pip3' as it is the standard for Python 3 on Raspberry Pi OS
    if command -v pip3 &> /dev/null; then
        sudo pip3 install $PYTHON_DEPS
    else
        echo "pip3 not found. Installing python3-pip..."
        sudo apt update
        sudo apt install -y python3-pip
        sudo pip3 install $PYTHON_DEPS
    fi
    echo "Dependencies installed."
}

# --- 3. INTERACTIVE ARDUINO DIAGNOSTICS ---
select_arduino_port() {
    echo "--- Arduino Diagnostics ---"
    echo "Scanning for connected Arduino/USB Serial devices..."
    
    # List devices commonly associated with Arduino
    ARDUINO_DEVICES=$(ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null)
    
    if [ -z "$ARDUINO_DEVICES" ]; then
        echo "No potential Arduino/USB devices found."
        echo "Please ensure the Arduino Uno is plugged in via USB."
    else
        echo "Found the following devices (the Python app will auto-select):"
        echo "$ARDUINO_DEVICES"
        echo "Please verify your Arduino is in this list."
    fi
    echo "---------------------------"
}

# --- 4. FILE AND DIRECTORY SETUP ---
setup_files() {
    echo "Setting up project directories and copying files..."

    # Ensure project directory exists
    sudo mkdir -p "$PROJECT_DIR"
    sudo mkdir -p "$PROJECT_DIR/templates"

    # Copy Python and HTML files (assuming they are in the current working directory)
    # Note: In a real environment, you'd pull these from a git repo.
    sudo cp app.py "$PROJECT_DIR/"
    sudo cp templates/index.html "$PROJECT_DIR/templates/"

    echo "Files copied successfully to $PROJECT_DIR."
}

# --- 5. SERVICE FILE GENERATION ---
create_service_file() {
    # Find the Python 3 executable path
    PYTHON_EXEC=$(which python3)
    if [ -z "$PYTHON_EXEC" ]; then
        echo "ERROR: python3 executable not found. Installation aborted."
        exit 1
    fi
    echo "Using Python executable: $PYTHON_EXEC"

    echo "Generating $SERVICE_NAME file..."

    # Check if service already exists
    if [ -f "$SERVICE_PATH" ]; then
        echo "$SERVICE_NAME already exists. Stopping and reloading..."
        sudo systemctl stop "$SERVICE_NAME" &>/dev/null
    fi

    # Create the service file using the found Python path and provided arguments
    sudo tee "$SERVICE_PATH" > /dev/null <<EOF
[Unit]
Description=Flask Plant Waterer Monitoring Service
After=network.target

[Service]
User=pi
WorkingDirectory=$PROJECT_DIR/
# Command to execute the Flask application:
# Arguments are: [sys.argv[1] = API_KEY] and [sys.argv[2] = CITY_NAME]
ExecStart=$PYTHON_EXEC $PROJECT_DIR/app.py "$API_KEY" "$CITY_NAME"
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    echo "$SERVICE_NAME created/updated successfully."
}

# --- 6. SERVICE DEPLOYMENT AND STARTUP ---
deploy_service() {
    echo "Deploying and starting systemd service..."

    # Reload the systemd daemon to recognize the new or updated service file
    sudo systemctl daemon-reload

    # Enable the service to start on boot
    sudo systemctl enable "$SERVICE_NAME"

    # Start the service immediately
    sudo systemctl start "$SERVICE_NAME"

    echo ""
    echo "--- DEPLOYMENT COMPLETE ---"
    echo "Service Status:"
    sudo systemctl status "$SERVICE_NAME" --no-pager
    echo ""
    echo "Access the dashboard by navigating to the Pi's IP address on port 5000:"
    echo "http://[Pi_IP_Address]:5000"
    echo "To view logs: sudo journalctl -u $SERVICE_NAME -f"
}

# --- MAIN EXECUTION FLOW ---
install_dependencies
select_arduino_port
setup_files
create_service_file
deploy_service

exit 0