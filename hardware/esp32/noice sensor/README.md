# LM393 Sound Sensor with ESP32

## Overview

The LM393 Sound Sensor is used to detect changes in sound/noise levels. In our **Smart Library Study-Zone Analyzer**, it is used to monitor the noise level of the study area.

> Note: This sensor provides a relative noise level, not an accurate dB measurement.

## Components

* ESP32
* LM393 Sound Sensor
* Jumper Wires
* Breadboard
* USB Cable

## Connections

| LM393 | ESP32    |
| ----- | -------- |
| VCC   | 3.3V     |
| GND   | GND      |
| AO    | GPIO 34  |
| DO    | Not Used |

## Working

The sensor detects sound through its microphone and sends an analog signal through **AO**. The ESP32 reads this signal using its ADC.

```text
Sound → LM393 → AO → ESP32 GPIO 34 → Noise Level
```

Open the **Serial Monitor at 115200 baud** and test the sensor with:

* Quiet environment
* Speaking
* Clapping
* Loud sound

Record the raw values and use them to calibrate the noise-level range.

## Project Use

The sensor will be used along with the **DHT11, LDR, and RFID** sensors to analyze the conditions of different study zones in the library.

## Limitations

* Does not provide accurate dB values.
* Readings vary between sensors.
* Calibration is required.
* Background noise can affect readings.
