#include <SPI.h>
#include <MFRC522.h>
#define SS_PIN 5
#define RST_PIN 22
MFRC522 rfid(SS_PIN, RST_PIN);
void setup() {
  Serial.begin(115200);
  SPI.begin();
  rfid.PCD_Init();
  Serial.println("RFID Reader Ready!");
  Serial.println("Place your RFID card/tag near the reader...");
}
void loop() {
  if (!rfid.PICC_IsNewCardPresent()) {
    return;
  }
  if (!rfid.PICC_ReadCardSerial()) {
    return;
  }
  Serial.print("Card UID: ");
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
  Serial.print("Card Type: ");
  MFRC522::PICC_Type piccType =
      rfid.PICC_GetType(rfid.uid.sak);
  Serial.println(rfid.PICC_GetTypeName(piccType));
  Serial.println("--------------------");
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(1000);
}
