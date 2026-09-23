# DHT11 Sensor with ESP32

## Objective

To interface the DHT11 temperature and humidity sensor
with the ESP32 and read temperature and humidity values.

## Components Required

- ESP32 Development Board
- DHT11 Sensor
- Breadboard
- Jumper Wires
- USB Cable
- Arduino IDE
- DHT Sensor Library

## Sensor Information

DHT11 is a digital temperature and humidity sensor.
It provides temperature and relative humidity readings
through a digital data pin.

## Pin Connections

| DHT11 | ESP32 |
|---|---|
| VCC | 3.3V |
| DATA | GPIO 15 |
| GND | GND |

## Working

The DHT11 sends temperature and humidity data to the
ESP32 through its digital data pin. The ESP32 reads the
values and displays them on the Serial Monitor.

## Program

See `dht11.ino`.

## Expected Output

Temperature: 34 °C (as per temp)
Humidity: 65 % (as per temp)

## Result

The DHT11 sensor was successfully interfaced with the
ESP32 and temperature and humidity values were displayed
on the Serial Monitor.

## Project Relevance

The DHT11 will later be used to monitor the environmental
conditions of different library study zones.
