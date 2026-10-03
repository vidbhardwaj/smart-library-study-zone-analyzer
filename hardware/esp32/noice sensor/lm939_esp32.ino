#define SOUND_PIN 34

void setup() {
  Serial.begin(115200);
}

void loop() {
  int soundValue = analogRead(SOUND_PIN);

  Serial.print("Raw Sound Value: ");
  Serial.println(soundValue);

  delay(500);
}