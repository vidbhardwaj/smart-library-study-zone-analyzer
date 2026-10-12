#include <SPI.h>
#include <MFRC522.h>
#include <DHT.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <vector>

// ==============================================================================
// Smart Library Study Zone Analyzer - Resilient Firmware (Antigravity Edition)
// Self-healing, non-blocking telemetry with automatic recovery & diagnostics
// ==============================================================================

// ---------- WiFi Configuration ----------
const char* ssid = "Vid Bhardwaj ";          // WiFi SSID
const char* password = "Vid@0636";           // WiFi Password
const char* serverUrl = "http://10.119.111.165:8000/readings"; // Backend FastAPI URL

// ---------- Hardware Pin Definitions ----------
#define SS_PIN    5   // RFID SDA / SS
#define RST_PIN   22  // RFID Reset
#define DHT_PIN   4   // DHT11 Data
#define SOUND_PIN 34  // Analog Sound Sensor (ADC1)
#define LDR_PIN   35  // Analog LDR Light Sensor (ADC1)
#define LED_PIN   2   // Onboard Status LED

#define DHT_TYPE DHT11
DHT dht(DHT_PIN, DHT_TYPE);
MFRC522 rfid(SS_PIN, RST_PIN);

// ---------- Study Zone & Occupancy Configuration ----------
const int ZONE_ID = 1;                    // Assigned study zone ID
const int ROOM_CAPACITY = 2;              // Maximum seating capacity
std::vector<String> activeUIDs;           // Track scanned UIDs inside room

// ---------- Timing & Resilience Controls ----------
unsigned long lastSendTime = 0;
unsigned long sendInterval = 5000;        // Base telemetry interval (5s)
unsigned long currentInterval = 5000;     // Adaptive interval
unsigned long lastWiFiCheck = 0;
const unsigned long wifiCheckInterval = 10000; // Check WiFi every 10s

// Last known valid sensor cache (neutralizes transient NaN glitches)
float lastValidTemp = 23.0;
float lastValidHum = 50.0;

// Helper: Convert RFID UID bytes to string
String getUID(MFRC522::Uid uid) {
  String s = "";
  for (byte i = 0; i < uid.size; i++) {
    if (uid.uidByte[i] < 0x10) s += "0";
    s += String(uid.uidByte[i], HEX);
    if (i < uid.size - 1) s += ":";
  }
  s.toUpperCase();
  return s;
}

// Self-healing Wi-Fi connection manager
void checkWiFiConnection() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI] Connection lost or connecting... attempting reconnection");
    WiFi.disconnect();
    WiFi.reconnect();
    unsigned long startWait = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startWait < 3000) {
      delay(200);
      Serial.print(".");
    }
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\n[WIFI] Successfully reconnected! IP: " + WiFi.localIP().toString());
    } else {
      Serial.println("\n[WIFI] Reconnection attempt timed out. Will retry next cycle.");
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.println("\n==================================================");
  Serial.println(" SMART LIBRARY STUDY ZONE ANALYZER - FIRMWARE v2.0");
  Serial.println(" Self-Balancing IoT Edge Node");
  Serial.println("==================================================");

  // Initialize Sensors & SPI
  SPI.begin();
  rfid.PCD_Init();
  dht.begin();
  Serial.println("[INIT] RFID & DHT11 initialized.");

  // Connect to Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("[WIFI] Connecting to SSID: ");
  Serial.println(ssid);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    digitalWrite(LED_PIN, HIGH);
    Serial.println("\n[WIFI] Connected! Assigned IP: " + WiFi.localIP().toString());
    Serial.print("[CONFIG] Backend Target: ");
    Serial.println(serverUrl);
  } else {
    Serial.println("\n[WIFI] Initial connection pending; loop will auto-reconnect.");
  }

  Serial.println("[STATUS] System Ready. Monitoring environmental conditions & RFID...");
}

void loop() {
  unsigned long now = millis();

  // 1. NON-BLOCKING RFID SCANNING (Zero latency for card taps)
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    String uidStr = getUID(rfid.uid);
    auto it = std::find(activeUIDs.begin(), activeUIDs.end(), uidStr);

    if (it == activeUIDs.end()) {
      // Person entering
      if (activeUIDs.size() < ROOM_CAPACITY) {
        activeUIDs.push_back(uidStr);
        Serial.println("\n[RFID ENTRY] Access Granted: UID " + uidStr);
        // Visual indicator flash
        digitalWrite(LED_PIN, LOW);
        delay(100);
        digitalWrite(LED_PIN, HIGH);
      } else {
        Serial.println("\n[RFID DENIED] Zone FULL (Capacity: " + String(ROOM_CAPACITY) + "): UID " + uidStr);
      }
    } else {
      // Person exiting
      activeUIDs.erase(it);
      Serial.println("\n[RFID EXIT] Checked Out: UID " + uidStr);
    }

    Serial.printf("[OCCUPANCY] Current Count: %d / %d\n", activeUIDs.size(), ROOM_CAPACITY);
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();

    // Trigger immediate send on RFID change
    lastSendTime = 0; 
  }

  // 2. PERIODIC WI-FI HEALTH CHECK
  if (now - lastWiFiCheck >= wifiCheckInterval) {
    lastWiFiCheck = now;
    if (WiFi.status() != WL_CONNECTED) {
      checkWiFiConnection();
    }
  }

  // 3. PERIODIC SENSOR SAMPLING & RESILIENT TELEMETRY TRANSMISSION
  if (now - lastSendTime >= currentInterval) {
    lastSendTime = now;

    // --- Read DHT11 with NaN protection ---
    float rawTemp = dht.readTemperature();
    float rawHum = dht.readHumidity();

    if (isnan(rawTemp)) {
      Serial.println("[DHT WARN] Temperature read NaN! Using cached fallback.");
    } else {
      lastValidTemp = rawTemp;
    }

    if (isnan(rawHum)) {
      Serial.println("[DHT WARN] Humidity read NaN! Using cached fallback.");
    } else {
      lastValidHum = rawHum;
    }

    // --- Sound Sensor (ADC1 Pin 34) ---
    int rawSound = analogRead(SOUND_PIN);
    // Map 12-bit ADC (0-4095) to calibrated noise level (0-100 dB estimate)
    int noiseLevel = constrain(map(rawSound, 0, 4095, 30, 95), 30, 100);

    // --- LDR Light Sensor (ADC1 Pin 35) ---
    int rawLight = analogRead(LDR_PIN);
    // Invert/map depending on LDR circuit (0-4095 -> 0-1000 Lux estimate)
    int lightLux = constrain(map(rawLight, 0, 4095, 50, 850), 0, 1000);

    int currentOccupancy = activeUIDs.size();

    // Print local readings
    Serial.printf("\n[SENSORS] Temp: %.1fC | Hum: %.1f%% | Light: %d Lux | Noise: %d dB | Occ: %d/%d\n",
                  lastValidTemp, lastValidHum, lightLux, noiseLevel, currentOccupancy, ROOM_CAPACITY);

    // Send HTTP POST if WiFi connected
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(serverUrl);
      http.setTimeout(4000); // 4-second timeout prevents freezing
      http.addHeader("Content-Type", "application/json");

      // Construct verified JSON payload
      String json = "{\"zone_id\":" + String(ZONE_ID) + ","
                    "\"temperature_c\":" + String(lastValidTemp, 1) + ","
                    "\"humidity_percent\":" + String(lastValidHum, 1) + ","
                    "\"light_lux\":" + String(lightLux) + ","
                    "\"noise_db\":" + String(noiseLevel) + ","
                    "\"occupancy\":" + String(currentOccupancy) + ","
                    "\"capacity\":" + String(ROOM_CAPACITY) + "}";

      int httpResponseCode = http.POST(json);

      if (httpResponseCode == 201 || httpResponseCode == 200) {
        // SUCCESS: Reset backoff to normal interval
        currentInterval = sendInterval;
        String response = http.getString();
        Serial.printf("[POST OK %d] Data acknowledged by backend!\n", httpResponseCode);
        Serial.println("  Server: " + response);
      } else if (httpResponseCode > 0) {
        // Server returned an HTTP error status code (e.g., 400, 404, 500)
        Serial.printf("[POST HTTP %d] Backend responded with error:\n", httpResponseCode);
        Serial.println("  Response: " + http.getString());
      } else {
        // Client-side failure (Timeout, Connection Refused, Network Lost)
        Serial.printf("[POST FAILED] Code: %d (%s)\n", httpResponseCode, http.errorToString(httpResponseCode).c_str());
        Serial.printf("  Target: %s (Check if PC backend is running)\n", serverUrl);

        // Self-balancing adaptive backoff (5s -> 10s -> 20s max)
        currentInterval = min(currentInterval * 2, (unsigned long)20000);
        Serial.printf("[BACKOFF] Backing off transmission interval to %lu ms\n", currentInterval);
      }

      http.end();
    } else {
      Serial.println("[OFFLINE] WiFi disconnected; telemetry queued for next cycle.");
    }
  }

  // Brief yield for RTOS task scheduler
  delay(20);
}
