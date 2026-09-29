# Practical 6 – RFID with ESP32

## Student Details

- **Name:** BHARDWAJ VID VIMALBHAI
- **Enrollment No.:** 12402110501065
- **Practical No.:** 6

## Aim

To interface an RFID (Radio Frequency Identification) module with
ESP32 and read the UID and card type of an RFID card/tag.

## Requirements

- ESP32 Development Board
- RFID RC522 Module
- RFID Card/Tag
- Breadboard
- Jumper Wires
- USB Cable
- Arduino IDE
- MFRC522 Library

## Introduction

RFID (Radio Frequency Identification) is a technology used to
identify objects or people using radio-frequency communication.

The RC522 RFID module works at 13.56 MHz and communicates with
the ESP32 using SPI (Serial Peripheral Interface) communication.

Each RFID card/tag has a unique identification number called a
UID (Unique Identifier). When a card is placed near the RFID
reader, the RC522 detects the card and sends its information to
the ESP32.

The ESP32 processes the received information and displays the
Card UID and Card Type on the Serial Monitor.

## Circuit Connections

| RC522 | ESP32 |
|---|---|
| SDA / SS | GPIO 5 |
| SCK | GPIO 18 |
| MOSI | GPIO 23 |
| MISO | GPIO 19 |
| IRQ | Not Connected |
| GND | GND |
| RST | GPIO 22 |
| 3.3V | 3.3V |

> **Note:** The RC522 operates at 3.3V. Do not connect it to 5V.

## Program

The Arduino program is available in:

`RFID_ESP32.ino`

The program initializes the SPI interface and RC522 module,
detects a new RFID card, reads its UID, identifies the card type,
and displays the information on the Serial Monitor.

## Working

1. ESP32 initializes the SPI communication.
2. The RC522 RFID module is initialized.
3. The system waits for an RFID card/tag.
4. When a card is detected, its UID is read.
5. The card type is identified using the UID/Sak information.
6. The UID and card type are displayed on the Serial Monitor.

## Output

The Serial Monitor displays the RFID reader status, card UID,
and card type.

Example:

```text
RFID Reader Ready!
Place your RFID card/tag near the reader...
Card UID: XX:XX:XX:XX
Card Type: MIFARE 1KB
--------------------