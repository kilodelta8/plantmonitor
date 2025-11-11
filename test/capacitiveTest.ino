// --- Wiring Setup ---
// Sensor VCC to Arduino 5V
// Sensor GND to Arduino GND
// Sensor AOUT (Analog Out) to Arduino Analog Pin A0

// Define the analog pin where the sensor's AOUT pin is connected
const int MOISTURE_SENSOR_PIN = A0;

void setup() {
  // Initialize serial communication at a standard baud rate
  // We'll use this to send data to the Raspberry Pi later, but for now, it's for calibration.
  Serial.begin(9600);
  
  // A small delay to ensure the sensor and serial are ready
  delay(100); 
  Serial.println("Capacitive Soil Moisture Sensor Test");
  Serial.println("------------------------------------");
}

void loop() {
  // Read the raw analog value from the sensor.
  // The Arduino's ADC converts the voltage (0V to 5V) into a number (0 to 1023).
  int sensorValue = analogRead(MOISTURE_SENSOR_PIN);
  
  // Print the raw value
  Serial.print("Raw Sensor Value: ");
  Serial.println(sensorValue);
  
  // We don't need super fast readings for soil, so a 2-second delay is fine.
  delay(2000); 
}