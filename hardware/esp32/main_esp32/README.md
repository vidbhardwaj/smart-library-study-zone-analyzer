# Combined Sensor Test – ESP32

## Overview

This program tests multiple sensors together using an **ESP32** for the **Smart Library Study-Zone Analyzer** project.

The following components are connected to the ESP32:

* RFID RC522
* DHT11 Temperature and Humidity Sensor
* LM393 Sound Sensor
* LDR Light Sensor

The program reads the sensor values and displays them on the **Serial Monitor**.

---

## Components Required

* ESP32 Development Board
* RFID RC522 Module
* RFID Card/Tag
* DHT11 Sensor
* LM393 Sound Sensor
* LDR Sensor/Module
* Breadboard
* Jumper Wires
* USB Cable

---

## Libraries Required

Only the following libraries are required:

```cpp
#include <SPI.h>
#include <MFRC522.h>
#include <DHT.h>
```

### Library Details

| Library     | Purpose                                  |
| ----------- | ---------------------------------------- |
| `SPI.h`     | SPI communication with RFID RC522        |
| `MFRC522.h` | Interface with RFID RC522                |
| `DHT.h`     | Read temperature and humidity from DHT11 |

`SPI.h` and `DHT.h` are normally available with the Arduino/ESP32 environment. The **MFRC522 library** needs to be installed through the Arduino IDE Library Manager if it is not already installed.

---

## Pin Connections

### RFID RC522

| RC522 Pin | ESP32   |
| --------- | ------- |
| SDA / SS  | GPIO 5  |
| SCK       | GPIO 18 |
| MOSI      | GPIO 23 |
| MISO      | GPIO 19 |
| RST       | GPIO 22 |
| 3.3V      | 3.3V    |
| GND       | GND     |

### DHT11

| DHT11 Pin | ESP32  |
| --------- | ------ |
| VCC       | 3.3V   |
| DATA      | GPIO 4 |
| GND       | GND    |

### LM393 Sound Sensor

| Sound Sensor Pin | ESP32         |
| ---------------- | ------------- |
| VCC              | 3.3V          |
| GND              | GND           |
| AO               | GPIO 34       |
| DO               | Not Connected |

The **AO (Analog Output)** pin is used to read the relative sound level.

### LDR

| LDR Pin | ESP32   |
| ------- | ------- |
| VCC     | 3.3V    |
| GND     | GND     |
| AO      | GPIO 35 |

> Pin connections for the LDR may vary depending on the module being used. Verify the labels on the actual module before connecting it.

---

## Working

The ESP32 initializes all four components when the program starts.

### 1. DHT11

The DHT11 provides:

* Temperature
* Humidity

The values are displayed in the Serial Monitor.

### 2. LM393 Sound Sensor

The analog output from the sound sensor is read using GPIO 34.

The ESP32 ADC provides a raw value from approximately:

```text
0 – 4095
```

The program converts this raw value into a relative noise value from:

```text
0 – 100
```

This value represents a **relative noise level**, not an actual measurement in decibels (dB).

### 3. LDR

The LDR provides an analog reading based on the surrounding light intensity.

The raw ADC value is converted into a relative light level from:

```text
0 – 100
```

### 4. RFID RC522

The RFID reader communicates with the ESP32 using SPI communication.

When an RFID card or tag is detected, its UID is displayed on the Serial Monitor.

---

## Serial Monitor Output

Set the Serial Monitor baud rate to:

```text
115200
```

Example output:

```text
======================================
 SMART LIBRARY STUDY ZONE ANALYZER
======================================
RFID       : READY
DHT11      : READY
Sound      : READY
LDR        : READY
--------------------------------------
Waiting for sensor data...

--------------- SENSOR DATA ---------------
Temperature : 28.00 °C
Humidity    : 65.00 %
Sound Raw   : 315
Noise Level : 7 %
LDR Raw     : 1850
Light Level : 45 %
```

When an RFID card is detected:

```text
******** RFID CARD DETECTED ********
Card UID    : XX:XX:XX:XX
************************************
```

---

## Important Note About Noise Level

The LM393 sound sensor used in this test does **not directly provide sound level in dB**.

The program currently converts the ADC value into a relative scale:

```text
0 – 100
```

Therefore, the output should be considered a **Relative Noise Level** rather than an actual percentage or dB measurement.

The conversion can later be calibrated according to the actual sensor readings obtained in the library environment.

---

## Project Relevance

This combined test is an initial hardware integration step for the **Smart Library Study-Zone Analyzer**.

The tested parameters will later be used for analyzing the study environment:

* Temperature
* Humidity
* Noise
* Light
* RFID-based identification/interaction

After individual sensor testing and calibration, the ESP32 can be connected to the backend system to send sensor data for storage, analysis, and dashboard visualization.

---

## File

```text
05_all_sensors/
└── final_firmware.ino
```

---

## Result

The ESP32 successfully reads data from the DHT11, LM393 sound sensor, LDR, and RFID RC522 and displays the readings on the Serial Monitor.
