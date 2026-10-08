#include <SPI.h>
#include <MFRC522.h>
#include <DHT.h>
// ---------- RFID ----------
#define SS_PIN 5
#define RST_PIN 22
MFRC522 rfid(SS_PIN, RST_PIN);
// ---------- DHT11 ----------
#define DHT_PIN 4
#define DHT_TYPE DHT11
DHT dht(DHT_PIN, DHT_TYPE);
// ---------- Sensors ----------
#define SOUND_PIN 34
#define LDR_PIN 35
void setup() {
  Serial.begin(115200);
  // Start RFID
  SPI.begin();
  rfid.PCD_Init();
  // Start DHT11
  dht.begin();
  Serial.println();
  Serial.println("======================================");
  Serial.println(" SMART LIBRARY STUDY ZONE ANALYZER");
  Serial.println("======================================");
  Serial.println("RFID       : READY");
  Serial.println("DHT11      : READY");
  Serial.println("Sound      : READY");
  Serial.println("LDR        : READY");
  Serial.println("--------------------------------------");
  Serial.println("Waiting for sensor data...");
  Serial.println();
}
void loop() {
  // ======================================
  // DHT11
  // ======================================
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  // ======================================
  // LM393 SOUND SENSOR
  // ======================================
  int soundValue = analogRead(SOUND_PIN);
  int noiseLevel = map(soundValue, 0, 4095, 0, 100);
  noiseLevel = constrain(noiseLevel, 0, 100);
  // ======================================
  // LDR
  // ======================================
  int lightValue = analogRead(LDR_PIN);
  int lightLevel = map(lightValue, 0, 4095, 0, 100);
  lightLevel = constrain(lightLevel, 0, 100);
  // ======================================
  // DISPLAY SENSOR DATA
  // ======================================
  Serial.println("--------------- SENSOR DATA ---------------");
  // Temperature and Humidity
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("DHT11       : ERROR");
  } else {
    Serial.print("Temperature : ");
    Serial.print(temperature);
    Serial.println(" °C");
    Serial.print("Humidity    : ");
    Serial.print(humidity);
    Serial.println(" %");
  }
  // Sound
  Serial.print("Sound Raw   : ");
  Serial.println(soundValue);
  Serial.print("Noise Level : ");
  Serial.print(noiseLevel);
  Serial.println(" %");
  // Light
  Serial.print("LDR Raw     : ");
  Serial.println(lightValue);
  Serial.print("Light Level : ");
  Serial.print(lightLevel);
  Serial.println(" %");
  // ======================================
  // RFID
  // ======================================
  if (rfid.PICC_IsNewCardPresent() &&
      rfid.PICC_ReadCardSerial()) {
    Serial.println();
    Serial.println("******** RFID CARD DETECTED ********");
    Serial.print("Card UID    : ");
    for (byte i = 0; i < rfid.uid.size; i++) {
      if (rfid.uid.uidByte[i] < 0x10) {
        Serial.print("0");
      }
      Serial.print(rfid.uid.uidByte[i], HEX);
      if (i < rfid.uid.size - 1) {
        Serial.print(":");
      }
    }
    Serial.println();
    Serial.println("************************************");
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
  }
  Serial.println();
  delay(2000);
}

