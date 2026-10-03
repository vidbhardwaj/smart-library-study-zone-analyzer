# LDR Light Sensor with ESP32

## Overview

The LDR module is used to detect the **light intensity** of the surrounding environment. In our **Smart Library Study-Zone Analyzer**, it is used to monitor the lighting conditions of study areas.

## Components

* ESP32
* LDR Sensor Module
* Jumper Wires
* Breadboard
* USB Cable

## Connections

| LDR Module | ESP32    |
| ---------- | -------- |
| VCC        | 3.3V     |
| GND        | GND      |
| AO         | GPIO 34  |
| DO         | Not Used |

## Working

The LDR changes its resistance according to the amount of light. The module provides an analog output through **AO**, which is read by the ESP32.

```text
Light → LDR → AO → ESP32 GPIO 34 → Light Reading
```

## Project Use

The LDR will be used to monitor the lighting conditions of different study zones along with the **DHT11, LM393 Sound Sensor, and RFID**.

## Note

The raw LDR value is not directly equal to **lux**. Calibration is required if an approximate lux value is needed.
