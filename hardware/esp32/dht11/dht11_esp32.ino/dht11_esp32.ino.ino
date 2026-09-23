#include "DHTesp.h"
// DHT11 pin connection
const int DHT_PIN = 15;  
DHTesp dhtSensor;
void setup() {
  Serial.begin(115200);
  dhtSensor.setup(DHT_PIN, DHTesp::DHT11);
  Serial.println("ESP32 + DHT11 Test");
}
void loop() {
  TempAndHumidity data = dhtSensor.getTempAndHumidity();
  float temperature = data.temperature;
  float humidity = data.humidity;
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("DHT11 reading failed!");
  } else {
    Serial.print("Temperature: ");
    Serial.print(temperature, 1);
    Serial.println(" °C");
    Serial.print("Humidity: ");
    Serial.print(humidity, 1);
    Serial.println(" %");
  }
  delay(2000); // wait 2 seconds before next reading
}
