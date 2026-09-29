import tkinter as tk
from tkinter import ttk
import cv2
import serial
import threading
import re
import time
from PIL import Image, ImageTk
from ultralytics import YOLO


# =========================
# SETTINGS
# =========================

PORT = "COM7"
BAUD = 115200

MODEL_PATH = "yolo11n.pt"
CAMERA_INDEX = 0


# =========================
# GLOBAL DATA
# =========================

current_angle = 0
current_distance = -1

serial_running = True
camera_running = True

latest_frame = None
detected_objects = []

data_lock = threading.Lock()


# =========================
# YOLO
# =========================

print("Loading YOLO model...")

model = YOLO(MODEL_PATH)

print("YOLO loaded.")


# =========================
# SERIAL THREAD
# =========================

def serial_reader():

    global current_angle
    global current_distance

    try:

        ser = serial.Serial(
            PORT,
            BAUD,
            timeout=1
        )

        time.sleep(2)

        print("ESP32 connected.")

        while serial_running:

            line = ser.readline().decode(
                "utf-8",
                errors="ignore"
            ).strip()

            if not line:
                continue

            print(line)

            match = re.search(
                r"Angle:\s*(\d+)\s*\|\s*Distance:\s*(\d+)\s*cm",
                line
            )

            if match:

                angle = int(match.group(1))
                distance = int(match.group(2))

                with data_lock:

                    current_angle = angle
                    current_distance = distance

    except Exception as e:

        print("SERIAL ERROR:", e)

    finally:

        try:
            ser.close()
        except:
            pass


# =========================
# CAMERA + YOLO
# =========================

def camera_thread():

    global latest_frame
    global detected_objects

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_MSMF)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():

        print("Camera could not be opened.")

        return

    while camera_running:

        ret, frame = cap.read()

        if not ret:
            continue

        # YOLO inference

        results = model(
            frame,
            verbose=False
        )

        objects = []

        for result in results:

            for box in result.boxes:

                confidence = float(
                    box.conf[0]
                )

                if confidence < 0.40:
                    continue

                class_id = int(
                    box.cls[0]
                )

                name = model.names[class_id]

                objects.append(
                    (name, confidence)
                )

        # Draw YOLO results

        annotated = results[0].plot()

        with data_lock:

            latest_frame = annotated

            detected_objects = objects

    cap.release()


# =========================
# GUI
# =========================

root = tk.Tk()

root.title(
    "ESP32 + YOLO Detection System"
)

root.geometry(
    "1200x700"
)

root.configure(
    bg="#101010"
)


# =========================
# TITLE
# =========================

title = tk.Label(
    root,
    text="ESP32 + YOLO LIVE DETECTION",
    font=("Arial", 22, "bold"),
    fg="white",
    bg="#101010"
)

title.pack(
    pady=10
)


# =========================
# MAIN FRAME
# =========================

main_frame = tk.Frame(
    root,
    bg="#101010"
)

main_frame.pack(
    fill="both",
    expand=True
)


# =========================
# CAMERA PANEL
# =========================

camera_frame = tk.Frame(
    main_frame,
    bg="#202020"
)

camera_frame.pack(
    side="left",
    padx=15,
    pady=15,
    fill="both",
    expand=True
)


camera_title = tk.Label(
    camera_frame,
    text="LIVE CAMERA / YOLO",
    font=("Arial", 15, "bold"),
    fg="white",
    bg="#202020"
)

camera_title.pack(
    pady=5
)


camera_label = tk.Label(
    camera_frame,
    bg="black"
)

camera_label.pack(
    padx=10,
    pady=10,
    fill="both",
    expand=True
)


# =========================
# RIGHT PANEL
# =========================

right_frame = tk.Frame(
    main_frame,
    bg="#181818",
    width=350
)

right_frame.pack(
    side="right",
    fill="y",
    padx=15,
    pady=15
)

right_frame.pack_propagate(False)


# =========================
# STATUS
# =========================

status_title = tk.Label(
    right_frame,
    text="SYSTEM STATUS",
    font=("Arial", 16, "bold"),
    fg="white",
    bg="#181818"
)

status_title.pack(
    pady=15
)


# Angle

angle_label = tk.Label(
    right_frame,
    text="ANGLE: 0°",
    font=("Arial", 18),
    fg="cyan",
    bg="#181818"
)

angle_label.pack(
    pady=10
)


# Distance

distance_label = tk.Label(
    right_frame,
    text="DISTANCE: -- cm",
    font=("Arial", 18),
    fg="cyan",
    bg="#181818"
)

distance_label.pack(
    pady=10
)


# Scanning

scan_label = tk.Label(
    right_frame,
    text="SCANNING: YES",
    font=("Arial", 18, "bold"),
    fg="lime",
    bg="#181818"
)

scan_label.pack(
    pady=10
)


# Detection

detection_label = tk.Label(
    right_frame,
    text="OBJECT: NOT DETECTED",
    font=("Arial", 17, "bold"),
    fg="lime",
    bg="#181818"
)

detection_label.pack(
    pady=10
)


# =========================
# RADAR CANVAS
# =========================

radar_title = tk.Label(
    right_frame,
    text="SCAN POSITION",
    font=("Arial", 14, "bold"),
    fg="white",
    bg="#181818"
)

radar_title.pack(
    pady=(25, 5)
)


radar = tk.Canvas(
    right_frame,
    width=300,
    height=180,
    bg="black",
    highlightthickness=1,
    highlightbackground="gray"
)

radar.pack(
    pady=5
)


# =========================
# RADAR DRAW
# =========================

def draw_radar(angle):

    radar.delete("all")

    cx = 150
    cy = 160
    radius = 130

    # semicircle

    radar.create_arc(
        cx - radius,
        cy - radius,
        cx + radius,
        cy + radius,
        start=0,
        extent=180,
        outline="green",
        width=2
    )

    # center line

    radar.create_line(
        cx - radius,
        cy,
        cx + radius,
        cy,
        fill="green"
    )

    # angle line

    import math

    rad = math.radians(angle)

    x = cx + radius * math.cos(
        math.pi - rad
    )

    y = cy - radius * math.sin(
        math.pi - rad
    )

    radar.create_line(
        cx,
        cy,
        x,
        y,
        fill="lime",
        width=3
    )

    radar.create_text(
        15,
        165,
        text="0°",
        fill="white"
    )

    radar.create_text(
        140,
        10,
        text="90°",
        fill="white"
    )

    radar.create_text(
        265,
        165,
        text="180°",
        fill="white"
    )


# =========================
# GUI UPDATE
# =========================

def update_gui():

    with data_lock:

        angle = current_angle
        distance = current_distance

        frame = latest_frame

        objects = detected_objects.copy()


    # Angle

    angle_label.config(
        text=f"ANGLE: {angle}°"
    )


    # Distance

    if distance >= 0:

        distance_label.config(
            text=f"DISTANCE: {distance} cm"
        )

    else:

        distance_label.config(
            text="DISTANCE: --"
        )


    # YOLO status

    if objects:

        names = ", ".join(
            sorted(
                set(
                    obj[0]
                    for obj in objects
                )
            )
        )

        detection_label.config(
            text=f"OBJECT: {names.upper()}",
            fg="red"
        )

    else:

        detection_label.config(
            text="OBJECT: NOT DETECTED",
            fg="lime"
        )


    # Radar

    draw_radar(angle)


    # Camera

    if frame is not None:

        frame_rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        image = Image.fromarray(
            frame_rgb
        )

        image.thumbnail(
            (750, 550)
        )

        photo = ImageTk.PhotoImage(
            image=image
        )

        camera_label.config(
            image=photo
        )

        camera_label.image = photo


    root.after(
        30,
        update_gui
    )


# =========================
# CLOSE
# =========================

def close_program():

    global serial_running
    global camera_running

    serial_running = False
    camera_running = False

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    close_program
)


# =========================
# START THREADS
# =========================

threading.Thread(
    target=serial_reader,
    daemon=True
).start()


threading.Thread(
    target=camera_thread,
    daemon=True
).start()


# Start GUI updates

update_gui()

root.mainloop()