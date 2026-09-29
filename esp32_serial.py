import serial
import re
import time

PORT = "COM7"
BAUD = 115200

print("Connecting to ESP32...")

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

print("ESP32 CONNECTED")
print("Reading data...\n")

try:
    while True:
        line = ser.readline().decode("utf-8", errors="ignore").strip()

        if not line:
            continue

        # Example:
        # Angle: 145 | Distance: 232 cm

        match = re.search(
            r"Angle:\s*(\d+)\s*\|\s*Distance:\s*(\d+)\s*cm",
            line
        )

        if match:
            angle = int(match.group(1))
            distance = int(match.group(2))

            print(f"ANGLE: {angle:3d}°   DISTANCE: {distance:4d} cm")

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    ser.close()
    print("Serial connection closed.")