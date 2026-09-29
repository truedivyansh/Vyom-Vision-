# Vyom Vision

Vyom Vision is a computer-vision and embedded-system prototype for detecting objects with a camera while an ESP32-based scanning system provides distance and servo-angle telemetry.

## System Overview

The system combines:

- **ESP32** for servo scanning and ultrasonic distance measurement
- **HC-SR04** ultrasonic sensor for distance sensing
- **Servo motor** for scanning through an angular range
- **Laptop webcam** for camera input
- **YOLO11n** for real-time object detection
- **OpenCV** for camera processing and image handling
- **PyQt5** for the industrial-style graphical interface
- **PySerial** for ESP32 serial communication

### Data Flow

```text
Camera
  ↓
OpenCV
  ↓
YOLO11n object detection
  ↓
PyQt5 GUI
  ↑
Serial telemetry
  ↑
ESP32
  ├── Servo motor
  └── HC-SR04 ultrasonic sensor
```

## Hardware Connections

| Component | ESP32 Pin |
|---|---:|
| Servo signal | GPIO 18 |
| HC-SR04 TRIG | GPIO 5 |
| HC-SR04 ECHO | GPIO 19 |
| Indicator LED | GPIO 2 |

Use a common ground between externally powered components and the ESP32.

**Important:** HC-SR04 Echo can be 5 V, while ESP32 GPIO is 3.3 V logic. Use an appropriate voltage divider or level shifter on the Echo signal.

## Software Setup

Python 3.12 is recommended for the current project environment.

Install dependencies:

```bash
pip install -r requirements.txt
```

The repository contains the YOLO model file:

```text
yolo11n.pt
```

## Running the GUI

From the project directory:

```bash
.env312\Scripts\python.exe industrial_gui.py
```

The current configuration uses:

- Serial port: `COM7`
- Baud rate: `115200`
- Camera index: `0`
- YOLO confidence threshold: `0.40`

These values may need to be changed for a different computer or hardware setup.

## ESP32 Firmware

The Arduino firmware is provided as:

```text
esp32run.ino
```

It controls the servo scan and ultrasonic measurements and sends telemetry over serial.

The firmware also supports these serial commands:

```text
STOP
RESUME
```

`STOP` pauses scanning and activates the local indicator LED. `RESUME` allows scanning to continue.

## Project Files

- `industrial_gui.py` - main PyQt5 application
- `integrated_gui.py` - integrated GUI version
- `integrated_gui_backup.py` - backup copy of the integrated GUI
- `esp32_serial.py` - ESP32 serial communication utility
- `yolo_webcam.py` - basic YOLO webcam test
- `esp32run.ino` - ESP32 Arduino firmware
- `yolo11n.pt` - YOLO11n model
- `requirements.txt` - Python dependencies
- `.gitignore` - Git exclusions

## Safety

This repository is intended as a sensing, computer-vision, telemetry, and demonstration prototype.

It does **not** implement automated weapon targeting or firing. External light/laser hardware should not be connected directly to ESP32 GPIO pins unless the electrical interface is known to be safe and appropriately isolated.

## Notes

- The pretrained `yolo11n.pt` model is a general-purpose object detector. It is not automatically a dedicated drone detector.
- Camera detection and ultrasonic sensing are separate sensing channels and can be combined at the application level.
- Servo angle and ultrasonic distance are useful for visualizing the scan state in the GUI.
