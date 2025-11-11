# College Project: Automated Plant Waterer and Monitor (Arduino & Raspberry Pi)

This document outlines the construction, component list, and deployment instructions for the Automated Plant Waterer and Monitor system, which uses an **Arduino Uno** for sensor reading and pump control, and a **Raspberry Pi 3 B+** running a **Flask web server** for monitoring, scheduling, and weather-based automation.

## 1. Required Components & Links

| **Component** | **Quantity** | **Key Specification / Type** | **Est. Cost** | **Link (Placeholder)** | 
| :--- | :---: | :--- | :--- | :--- |
| **Microcontroller** | 1 | Arduino Uno R3 | Low | [Arduino Uno](https://www.google.com/search?q=https://www.amazon.com/dp/B074Q61GCR) | 
| **Server** | 1 | Raspberry Pi 3 B+ (or equivalent) | Medium | [Raspberry Pi 3 B+](https://www.google.com/search?q=https://www.amazon.com/dp/B07BCCMDBV) | 
| **Soil Sensor** | 1 | Capacitive Soil Moisture Sensor v1.2 | Low | [Capacitive Sensor](https://www.google.com/search?q=https://www.amazon.com/dp/B09BMVS366) | 
| **Temp/Humidity** | 1 | DHT11 or DHT22 | Low | [DHT Sensor](https://www.google.com/search?q=https://www.amazon.com/dp/B07QL452N8) | 
| **Actuator** | 1 | 5V DC Mini Submersible Water Pump | Low | [Mini Water Pump](https://www.google.com/search?q=https://www.amazon.com/dp/B082L4W243) | 
| **Driver** | 1 | 5V 1-Channel Relay Module | Low | [1-Channel Relay](https://www.google.com/search?q=https://www.amazon.com/dp/B07D381283) | 
| **Tubing** | \~1m | Silicone Tubing (must fit pump nozzle) | Low | [Silicone Tubing](https://www.google.com/search?q=https://www.amazon.com/dp/B07B1Y9QYQ) | 
| **Wiring** | Various | Jumper Wires (M/M, M/F), Breadboard | Low | [Jumper Wires](https://www.google.com/search?q=https://www.amazon.com/dp/B01F3J2I7G) | 
| **Power** | 1 | 5V/2A power supply for pump (optional but recommended) | Low | | 

## 2. Hardware Assembly and Wiring

Connect all components to the **Arduino Uno** as follows. The Arduino will be powered by the USB cable connected to the Raspberry Pi.

| **Component** | **Component Pin** | **Arduino Uno Pin** | **Purpose** | 
| :--- | :--- | :--- | :--- |
| **Capacitive Sensor** | VCC | 5V | Power | 
| **Capacitive Sensor** | GND | GND | Ground | 
| **Capacitive Sensor** | AOUT | **A0 (Analog)** | Read soil moisture level | 
| **DHT11/DHT22** | Data Pin | **Digital Pin 4** | Read temperature/humidity | 
| **Relay Module** | VCC | 5V | Power relay circuit | 
| **Relay Module** | GND | GND | Ground | 
| **Relay Module** | IN (Signal) | **Digital Pin 7** | Control pump ON/OFF | 
| **Water Pump** | Positive (+) | Relay Terminal: **NO** (or COM) | Connects pump to external power via switch | 
| **Water Pump** | Negative (-) | External Power Supply GND | Completes pump power circuit | 

## 3. Arduino Code Upload (`plant_controller.ino`)

The Arduino runs the embedded code that communicates with the Pi over USB Serial.

1. **Install Library:** Open the Arduino IDE. Go to **Sketch > Include Library > Manage Libraries...** and install the **"DHT sensor library" by Adafruit**.

2. **Open Code:** Copy the full contents of `plant_controller.ino` into a new Arduino sketch.

3. **Upload:** Connect the Arduino Uno to your PC (or Mac). Select the correct Board (`Arduino Uno`) and Port. Click **Upload**.

4. **Disconnect:** After successful upload, **disconnect the Arduino** from the PC.

## 4. Raspberry Pi Deployment (Flask Server)

The Flask app (`app.py`) runs the server, gets weather data, and sends commands to the Arduino via the USB cable.

### 4.1. File Setup (Manual or Clone)

**Option A: Clone Repository (Recommended for Re-runs)**

1. Log in to your Raspberry Pi via SSH or terminal.

2. Install Git if necessary: `sudo apt install git`.

3. Clone your project repository (assuming you push your files there):

   `
   git clone [https://your.repo.url/startrack-waterer.git](https://your.repo.url/startrack-waterer.git) /home/pi/plant-waterer
   cd /home/pi/plant-waterer
`

**Option B: Manual Copy/Create**

1.  Create the directory structure: `mkdir -p /home/pi/plant-waterer/templates`

2.  Copy `app.py`, `install.sh`, and `templates/index.html` into `/home/pi/plant-waterer/`.

3.  Ensure `install.sh` is executable: `chmod +x install.sh`

### 4.2. Run the Installer

1.  **Plug in the Arduino Uno** to one of the Raspberry Pi's USB ports. The Pi will power the Arduino.

2.  Run the installer script using `sudo`, your **OpenWeatherMap API Key**, and your **City Name** (in quotes if it contains a space).

    ```bash
    sudo ./install.sh [YOUR_API_KEY] "New York"
    ```

    The script will:

      * Install Python dependencies (`Flask`, `pyserial`, `requests`).

      * Find the `python3` executable path.

      * Create the systemd service (`plant_waterer.service`).

      * **The interactive diagnostic tool will run, allowing you to confirm the Arduino device path.**

      * Start the Flask application automatically.

### 4.3. Verification and Access

1.  **Check Status:** Verify the service is running:

    `
    sudo systemctl status plant_waterer.service
    `

2.  **Check Logs:** View real-time output (including serial data and watering triggers):

    `
    sudo journalctl -u plant_waterer.service -f
    `

3.  **Access Dashboard:** Open a browser on any device on the same network and navigate to the Pi's IP address on port 5000:

    `
    http://[Your.Pi.IP.Address]:5000
    `

## 5\. Next Steps / Calibration

  * **Calibration:** Fine-tune the watering logic in `app.py` (`MOISTURE_THRESHOLD`, `DRY_VALUE_MAX`, `WET_VALUE_MIN`) based on the raw sensor values you observe in the logs for your specific soil.

