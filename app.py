# **********************************************************************
# @file   app.py
# @author John Durham
# @date   10/27/2025
# @brief  This web application monitors soil moisture, temperature, and humidity
#         using an Arduino connected via USB serial. It fetches real-time weather
#         data from OpenWeatherMap to make intelligent watering decisions.
#         The app provides a web dashboard for monitoring and manual control.
# **********************************************************************


import serial
import time
import threading
import requests
import json
import sys 
from flask import Flask, render_template, jsonify, request, flash
from datetime import datetime
import serial.tools.list_ports 
import random 

# --- 1. CONFIGURATION ---
# IMPORTANT: These values are read from command-line arguments when using install.sh
BAUD_RATE = 9600
WEATHER_API_INTERVAL_SECONDS = 3600  # Check weather once per hour (3600 seconds)
SCHEDULER_INTERVAL_SECONDS = 60      # Check watering conditions every minute

# OpenWeatherMap API Configuration (Sign up for a free key)

# Check if an API key (sys.argv[1]) and City Name (sys.argv[2]) were passed
if len(sys.argv) > 2:
    API_KEY = sys.argv[1]
    CITY_NAME = sys.argv[2]
    print(f"API Key loaded from command-line. City set to: {CITY_NAME}")
elif len(sys.argv) > 1:
    API_KEY = sys.argv[1]
    CITY_NAME = "London" # Default if only API key is provided
    print("WARNING: Only API Key provided. Using default city: London.")
else:
    # FALLBACK: Use placeholders if no arguments are provided
    API_KEY = "YOUR_OPENWEATHERMAP_API_KEY" 
    CITY_NAME = "London"
    print("WARNING: Using default API Key and City. Pass key and city as arguments.")

WEATHER_URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY_NAME}&appid={API_KEY}&units=metric"

# Watering Logic Thresholds (Update these after calibrating your Arduino)
MOISTURE_THRESHOLD = 500  # If raw value is > 500 (drier), trigger water
DRY_VALUE_MAX = 650       # Your MAX DRY value from calibration (e.g., sensor in air)
WET_VALUE_MIN = 300       # Your MIN WET value from calibration (e.g., sensor in water)
WEATHER_RAIN_CHANCE_DELAY = 30  # If weather forecast predicts > 30% chance of rain, delay automatic watering

WATERING_DURATION_SECONDS = 3 # How long the pump runs when activated

# --- 2. GLOBAL STATE ---
# Shared dictionary to hold the latest sensor readings and status
system_state = {
    'moisture_raw': 0,
    'moisture_percent': 0,
    'temp_c': 0.0,
    'temp_f': 0.0,
    'humidity': 0.0,
    'last_update': 'N/A',
    'weather_desc': 'Fetching...',
    'weather_rain': False,
    'last_water': 'N/A',
    'auto_watering_enabled': True,
    'arduino_connected': False # New flag for connection status
}

# Variable for the Serial Connection object
ser = None

# --- 3. SERIAL COMMUNICATION THREAD ---

def find_arduino_port():
    """Searches for a connected Arduino device."""
    # List all available serial ports
    ports = list(serial.tools.list_ports.comports())
    
    for port in ports:
        # Check for common Arduino identifiers (adjust if necessary for your clone/board)
        if 'Arduino' in port.description or 'USB Serial' in port.description or 'ACM' in port.device:
            print(f"Found Arduino device on port: {port.device}")
            return port.device
            
    return None


def read_serial_thread():
    """Continuously reads sensor data from the Arduino via USB serial."""
    global system_state, ser

    # Loop to continuously try finding and connecting to the Arduino
    while ser is None:
        port_path = find_arduino_port()
        if port_path:
            try:
                ser = serial.Serial(port_path, BAUD_RATE, timeout=1)
                time.sleep(2) # Wait for the Arduino to reset
                ser.flushInput()
                system_state['arduino_connected'] = True
                print(f"Serial connection established on {port_path}")
                break
            except serial.SerialException as e:
                print(f"ERROR: Could not open serial port {port_path}. Retrying in 5s.")
                ser = None 
                time.sleep(5)
                system_state['arduino_connected'] = False
        else:
            print("Arduino not found. Simulating sensor data for testing. Retrying scan in 10s...")
            # If no Arduino found, we simulate data to keep the Flask app running
            system_state['moisture_raw'] = random.randint(400, 700)
            system_state['temp_c'] = random.uniform(18.0, 28.0)
            system_state['humidity'] = random.uniform(30.0, 60.0)
            system_state['last_update'] = datetime.now().strftime("%H:%M:%S")
            time.sleep(10)
            system_state['arduino_connected'] = False
            
    # Main reading loop once connection is established
    while True:
        try:
            if ser and ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip() 
                
                # Expected format from Arduino: MOISTURE_RAW,TEMP_C,HUMIDITY_PCT
                if line:
                    parts = line.split(',')
                    if len(parts) == 3:
                        moisture_raw = int(parts[0])
                        temp_c = float(parts[1])
                        humidity = float(parts[2])
                        
                        # Update global state
                        system_state['moisture_raw'] = moisture_raw
                        system_state['temp_c'] = temp_c
                        system_state['temp_f'] = (temp_c * 9/5) + 32 # Convert to Fahrenheit
                        system_state['humidity'] = humidity
                        system_state['last_update'] = datetime.now().strftime("%H:%M:%S")

                        # Calculate relative moisture percentage (for display)
                        range_span = DRY_VALUE_MAX - WET_VALUE_MIN
                        clamped_value = max(WET_VALUE_MIN, min(DRY_VALUE_MAX, moisture_raw))
                        moisture_pct = 100 - int(((clamped_value - WET_VALUE_MIN) / range_span) * 100)
                        system_state['moisture_percent'] = max(0, min(100, moisture_pct))

        except Exception as e:
            print(f"Error reading serial data ({e}). Connection lost. Attempting to re-find port.")
            ser = None # Reset serial connection on error to trigger re-connect
            system_state['arduino_connected'] = False
            # Break the inner loop to restart the port finding logic
            break 
        
        time.sleep(1)


def send_command_to_arduino(command):
    """Sends a command string to the Arduino (e.g., "WET" or "LIGHT ON")."""
    if ser and ser.is_open:
        try:
            # Commands MUST end with a newline character (\n) for Arduino's readline() to work
            ser.write(f"{command}\n".encode('utf-8'))
            print(f"Command sent to Arduino: {command}")
            return True
        except Exception as e:
            print(f"Failed to send command: {e}")
            return False
    else:
        print(f"ERROR: Cannot send command '{command}'. Serial connection is not open.")
        return False

# --- 4. WEATHER & SCHEDULE LOGIC THREADS ---

def update_weather_thread():
    """Fetches real-time weather data from OpenWeatherMap."""
    global system_state
    
    # We use exponential backoff for API retries (1s, 2s, 4s, 8s, 16s) 
    max_retries = 5 
    
    while True:
        if API_KEY == "YOUR_OPENWEATHERMAP_API_KEY":
            # Skip API call if key is still default
            print("Weather API key placeholder detected. Skipping API call.")
            time.sleep(WEATHER_API_INTERVAL_SECONDS)
            continue
            
        for attempt in range(max_retries):
            try:
                response = requests.get(WEATHER_URL, timeout=10)
                response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)
                data = response.json()
                
                # Check for weather conditions that indicate precipitation or high cloud cover
                # OpenWeatherMap uses a group ID for main weather condition. Group 5xx is Rain.
                weather_main = data['weather'][0]['main']
                weather_desc = data['weather'][0]['description']
                
                # Simple check for Rain/Snow/Drizzle (Group IDs 2xx, 3xx, 5xx, 6xx)
                # You can enhance this with forecast data if using a different API endpoint.
                is_raining = (data['weather'][0]['id'] // 100 in [2, 3, 5, 6])
                
                system_state['weather_desc'] = weather_desc.capitalize()
                system_state['weather_rain'] = is_raining
                print(f"Weather Update: {weather_desc}. Rain Check: {is_raining}.")
                break # Success! Break the retry loop
                
            except requests.exceptions.RequestException as e:
                print(f"Weather API request failed (Attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(2 ** attempt) # Exponential backoff
            except Exception as e:
                print(f"Error parsing weather data: {e}")
                break # Give up on current cycle

        time.sleep(WEATHER_API_INTERVAL_SECONDS)


def auto_watering_scheduler():
    """Checks conditions and triggers watering if needed."""
    global system_state
    
    # Wait for the system to settle before starting automation
    time.sleep(15) 
    
    while True:
        if system_state['auto_watering_enabled']:
            
            # Condition 1: Is the soil dry enough?
            is_dry = system_state['moisture_raw'] > MOISTURE_THRESHOLD
            
            # Condition 2: Is it raining or about to rain?
            is_rain_delay = system_state['weather_rain']
            
            # Check if all conditions are met
            if is_dry and not is_rain_delay:
                print("--- AUTO WATERING TRIGGERED ---")
                print(f"  Moisture Raw ({system_state['moisture_raw']}) is above threshold ({MOISTURE_THRESHOLD}).")
                
                # Send the "WET" command to the Arduino
                success = send_command_to_arduino("WET")
                
                if success:
                    # Update state and wait for the pump cycle to complete
                    system_state['last_water'] = datetime.now().strftime("%H:%M:%S - AUTO")
                    time.sleep(WATERING_DURATION_SECONDS + 1) # Wait for pump duration + 1s buffer
                
            elif is_dry and is_rain_delay:
                print(f"AUTO-WATERING SKIPPED: Soil is dry but weather is {system_state['weather_desc']} (Rain Delay active).")
            
        time.sleep(SCHEDULER_INTERVAL_SECONDS)


# --- 5. FLASK APPLICATION SETUP ---

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_testing' # Required for flash messages

# Route for the main dashboard
@app.route('/')
def index():    
    """Renders the main monitoring dashboard."""
    # Pass the current system state to the HTML template
    if not system_state['arduino_connected']:
        # Use flash to send a message to the template
        flash('Arduino not connected. Please check the USB connection and ensure the device has power.', 'danger')
    return render_template('index.html', state=system_state)

# Route to get the current sensor data (for JavaScript updates)
@app.route('/data', methods=['GET'])
def get_data():
    """Returns the current system state as JSON."""
    return jsonify(system_state)

# Route for manual watering control
@app.route('/water_manual', methods=['POST'])
def water_manual():
    """Triggers the pump manually from the web UI."""
    print("Manual watering requested...")
    
    # Send the "WET" command to the Arduino
    success = send_command_to_arduino("WET")
    
    if success:
        system_state['last_water'] = datetime.now().strftime("%H:%M:%S - MANUAL")
        # Simulate pump run time for immediate feedback
        # NOTE: This blocks the current web request for 4 seconds, fine for a small project.
        time.sleep(WATERING_DURATION_SECONDS + 1) 
        return jsonify({'status': 'success', 'message': 'Manual watering initiated.'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Serial connection not available. Check Arduino power.'}), 500

# Route to toggle automatic watering
@app.route('/toggle_auto', methods=['POST'])
def toggle_auto():
    """Toggles the automatic watering schedule on/off."""
    system_state['auto_watering_enabled'] = not system_state['auto_watering_enabled']
    
    if system_state['auto_watering_enabled']:
        message = "Automatic watering ENABLED."
    else:
        message = "Automatic watering DISABLED."
        
    print(message)
    return jsonify({'status': 'success', 'message': message, 'enabled': system_state['auto_watering_enabled']}), 200

# --- 6. START THREADS AND FLASK ---

if __name__ == '__main__':
    # Start the continuous Arduino reader thread
    serial_thread = threading.Thread(target=read_serial_thread)
    serial_thread.daemon = True 
    serial_thread.start()

    # Start the weather update thread
    weather_thread = threading.Thread(target=update_weather_thread)
    weather_thread.daemon = True
    weather_thread.start()

    # Start the auto-watering logic thread
    scheduler_thread = threading.Thread(target=auto_watering_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    # Start the Flask web server on all interfaces (0.0.0.0)
    # The Pi's IP address (e.g., 192.168.1.100:5000) will be accessible
    app.run(host='0.0.0.0', port=5000, debug=False)