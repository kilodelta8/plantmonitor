#include <DHT.h>

// --- 1. PIN DEFINITIONS ---
const int MOISTURE_PIN = A0;   // Capacitive Moisture Sensor AOUT pin
const int DHT_PIN = 4;         // DHT11 or DHT22 Data pin
const int RELAY_PIN = 7;       // Single-channel Relay signal pin

// Define the sensor type (DHT11 is faster/cheaper, DHT22 is more accurate)
#define DHTTYPE DHT11          
DHT dht(DHT_PIN, DHTTYPE);

// --- 2. ACTUATOR CONTROL CONSTANTS ---
// MOST cheap relays are LOW-level triggered (LOW = ON, HIGH = OFF)
const int RELAY_ON = LOW;      
const int RELAY_OFF = HIGH;    

// The Python server specifies the duration, but we'll use this if running manually
const unsigned long WATERING_DURATION_MS = 3000; // 3 seconds of watering

// --- 3. TIMING & DATA VARIABLES ---
const long SERIAL_REPORT_INTERVAL = 1000; // Report data every 1 second
unsigned long previousMillis = 0;

// Variables to hold sensor data
int rawMoisture = 0;
float temperatureC = 0.0;
float humidityPct = 0.0;

// --- 4. SETUP FUNCTION ---
void setup() {
  // Initialize serial communication for data transfer with the Raspberry Pi
  Serial.begin(9600); 

  // Initialize the DHT sensor
  dht.begin();
  
  // Configure the relay pin as an output
  pinMode(RELAY_PIN, OUTPUT);
  
  // Ensure the pump is OFF at startup
  digitalWrite(RELAY_PIN, RELAY_OFF);

  Serial.println("Arduino Plant Controller Initialized.");
}

// --- 5. MAIN LOOP ---
void loop() {
  // --- Task A: Read Sensors (Non-blocking timing) ---
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= SERIAL_REPORT_INTERVAL) {
    previousMillis = currentMillis; 
    
    // 1. Read DHT Sensor (Temperature and Humidity)
    // Reading humidity and temperature takes about 250ms!
    humidityPct = dht.readHumidity();
    temperatureC = dht.readTemperature(); 
    
    // Check if any reading failed and use the last valid value or 0
    if (isnan(humidityPct) || isnan(temperatureC)) {
        // If sensor read failed, print a message but maintain last values
        Serial.println("DHT Sensor Read Failed!");
        humidityPct = 0.0; // Reset to 0 if failed to avoid garbage data (optional)
        temperatureC = 0.0;
    }

    // 2. Read Moisture Sensor (Analog Value)
    rawMoisture = analogRead(MOISTURE_PIN);

    // 3. Send Data to Raspberry Pi (Python)
    // Format: MOISTURE_RAW,TEMP_C,HUMIDITY_PCT
    Serial.print(rawMoisture);
    Serial.print(",");
    Serial.print(temperatureC, 1); // 1 decimal place
    Serial.print(",");
    Serial.println(humidityPct, 1); // 1 decimal place, ends with newline
  }
  
  // --- Task B: Handle Serial Commands from Pi (Non-blocking check) ---
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // Read until newline
    command.trim(); // Remove any leading/trailing whitespace

    // Check for the "WET" command sent by the Python server
    if (command.equals("WET")) {
      Serial.println("Command Received: WET (Watering)");
      activatePump(WATERING_DURATION_MS); // Run pump for 3 seconds
    }
    // You could add a "LIGHT ON" command here later if you add the light!
  }
}

// --- 6. ACTUATOR FUNCTION ---
void activatePump(unsigned long duration) {
  // Turn the pump ON
  digitalWrite(RELAY_PIN, RELAY_ON);
  
  // Use a delay here to ensure the pump runs for the specified time
  // Since this is triggered by the Pi, it's okay to block loop momentarily
  delay(duration); 
  
  // Turn the pump OFF
  digitalWrite(RELAY_PIN, RELAY_OFF);
  Serial.println("Watering cycle complete. Pump OFF.");
}