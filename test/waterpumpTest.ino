// Define the digital pin the relay's signal wire (IN) is connected to.
const int RELAY_PIN = 7;

// Define the state needed to ACTIVATE the relay. 
// 99% of cheap relay modules are "Low-Level Triggered," meaning:
// LOW (0V) = ON (Activates Relay)
// HIGH (5V) = OFF (Deactivates Relay)
const int RELAY_ON = LOW;
const int RELAY_OFF = HIGH;

void setup() {
  // Set the Relay Pin as an output
  pinMode(RELAY_PIN, OUTPUT);

  // Ensure the relay is OFF (pump is NOT running) at startup
  digitalWrite(RELAY_PIN, RELAY_OFF);

  Serial.begin(9600);
  Serial.println("Water Pump Relay Test Sketch");
  Serial.println("----------------------------");
}

void loop() {
  // 1. Turn the Pump ON (Activate Relay)
  digitalWrite(RELAY_PIN, RELAY_ON);
  Serial.println("Pump ON for 3 seconds...");
  
  // Run the pump for 3 seconds
  delay(3000); 

  // 2. Turn the Pump OFF (Deactivate Relay)
  digitalWrite(RELAY_PIN, RELAY_OFF);
  Serial.println("Pump OFF. Waiting 5 seconds...");
  
  // Wait for 5 seconds before repeating the test
  delay(5000); 
}