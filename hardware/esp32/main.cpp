// Assignee: Vid Bhardwaj (IoT, ESP32 & Hardware)
// Hardware code for ESP32

#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 Initialized");
  // Initialize sensors here
}

void loop() {
  // Read sensor data here
  // Send data to backend API
  delay(2000);
}
