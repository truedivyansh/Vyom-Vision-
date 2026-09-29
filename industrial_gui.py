import sys
import cv2
import serial
import threading
import math
import re
import time
from ultralytics import YOLO

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame
)

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

import serial
from ultralytics import YOLO


# =========================================================
# SETTINGS
# =========================================================

SERIAL_PORT = "COM7"
BAUD_RATE = 115200

CAMERA_INDEX = 0

MODEL_PATH = "yolo11n.pt"

CONFIDENCE = 0.40


# =========================================================
# GLOBAL DATA
# =========================================================

current_angle = 0
current_distance = -1

serial_running = True
camera_running = True


# =========================================================
# YOLO MODEL
# =========================================================

print("Loading YOLO model...")

model = YOLO(MODEL_PATH)

print("YOLO model loaded.")


# =========================================================
# SERIAL THREAD
# =========================================================
def send_esp32_command(command):
    global ser

    if ser is not None and ser.is_open:
        ser.write((command + "\n").encode())
        print("SENT:", command)
        
class SerialWorker(QThread):


    data_received = pyqtSignal(int, int)
    connection_status = pyqtSignal(str)

    def run(self):

        global serial_running
        global ser 

        ser = None

        try:

            print("Connecting to ESP32...")

            ser = serial.Serial(
                SERIAL_PORT,
                BAUD_RATE,
                timeout=1
            )

            time.sleep(2)

            self.connection_status.emit("ESP32 CONNECTED")

            print("ESP32 connected.")

            while serial_running:

                line = ser.readline().decode(
                    "utf-8",
                    errors="ignore"
                ).strip()

                if not line:
                    continue

                print(line)

                # -------------------------------------------------
                # Supports:
                # Angle: 113 | Distance: 235 cm
                # ANGLE: 113° DISTANCE: 235 cm
                # -------------------------------------------------

                match = re.search(
                    r"(?:Angle|ANGLE)\s*:?\s*(\d+).*?"
                    r"(?:Distance|DISTANCE)\s*:?\s*(\d+)",
                    line
                )

                if match:

                    angle = int(match.group(1))
                    distance = int(match.group(2))

                    self.data_received.emit(
                        angle,
                        distance
                    )

        except Exception as e:

            print("SERIAL ERROR:", e)

            self.connection_status.emit(
                "ESP32 DISCONNECTED"
            )

        finally:

            if ser:

                try:
                    ser.close()
                except:
                    pass


# =========================================================
# CAMERA + YOLO THREAD
# =========================================================

class CameraWorker(QThread):

    frame_ready = pyqtSignal(object, list)
    camera_status = pyqtSignal(str)

    def run(self):

        global camera_running

        print("Opening webcam...")

        # IMPORTANT:
        # Webcam = 0
        # DroidCam = 1
        cap = cv2.VideoCapture(
            CAMERA_INDEX
        )

        if not cap.isOpened():

            print("Webcam could not be opened.")

            self.camera_status.emit(
                "CAMERA ERROR"
            )

            return

        self.camera_status.emit(
            "CAMERA ONLINE"
        )

        print("Webcam connected.")

        # -------------------------------------------------
        # Resolution
        # -------------------------------------------------

        cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            640
        )

        cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            480
        )

        while camera_running:

            ret, frame = cap.read()

            if not ret:

                continue

            # -------------------------------------------------
            # YOLO
            # -------------------------------------------------

            try:

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

                        if confidence < CONFIDENCE:

                            continue

                        class_id = int(
                            box.cls[0]
                        )

                        name = model.names[
                            class_id
                        ]

                        objects.append(
                            (
                                name,
                                confidence
                            )
                        )

                # -------------------------------------------------
                # Draw detections
                # -------------------------------------------------

                annotated = results[0].plot()

                self.frame_ready.emit(
                    annotated,
                    objects
                )

            except Exception as e:

                print(
                    "YOLO ERROR:",
                    e
                )

                self.frame_ready.emit(
                    frame,
                    []
                )

        cap.release()

        print("Webcam closed.")


# =========================================================
# MAIN WINDOW
# =========================================================

class IndustrialGUI(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "VYOM VISION | ANTI-DRONE SYSTEM"
        )

        self.resize(
            1400,
            800
        )

        self.setMinimumSize(
            1100,
            650
        )

        self.angle = 0
        self.distance = -1

        self.objects = []

        self.setup_ui()

        self.start_threads()

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_radar
        )

        self.timer.start(
            50
        )


    # =====================================================
    # UI SETUP
    # =====================================================

    def setup_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        central.setStyleSheet(
            """
            QWidget {
                background-color: #07111f;
                color: #e8f0f7;
                font-family: Segoe UI;
            }

            QFrame {
                background-color: #0d1b2a;
                border: 1px solid #20364d;
                border-radius: 6px;
            }

            QLabel {
                color: #e8f0f7;
            }
            """
        )

        main = QGridLayout(
            central
        )

        main.setContentsMargins(
            18,
            15,
            18,
            15
        )

        main.setSpacing(
            12
        )


        # =================================================
        # HEADER
        # =================================================

        header = QFrame()

        header_layout = QVBoxLayout(
            header
        )

        header_layout.setContentsMargins(
            18,
            12,
            18,
            12
        )

        title = QLabel(
            "VYOM VISION"
        )

        title.setStyleSheet(
            """
            color: #ffffff;
            font-size: 28px;
            font-weight: 700;
            """
        )

        subtitle = QLabel(
            "HIGH ALTITUDE ANTI-DRONE DETECTION & SURVEILLANCE SYSTEM"
        )

        subtitle.setStyleSheet(
            """
            color: #7f9bb5;
            font-size: 11px;
            letter-spacing: 1px;
            """
        )

        header_layout.addWidget(
            title
        )

        header_layout.addWidget(
            subtitle
        )

        main.addWidget(
            header,
            0,
            0,
            1,
            3
        )


        # =================================================
        # CAMERA PANEL
        # =================================================

        camera_panel = self.make_panel(
            "LIVE EO/IR CAMERA FEED"
        )

        camera_layout = camera_panel.layout()

        self.camera_view = QLabel(
            "CAMERA FEED\n\nWaiting for webcam..."
        )

        self.camera_view.setAlignment(
            Qt.AlignCenter
        )

        self.camera_view.setMinimumSize(
            500,
            350
        )

        self.camera_view.setStyleSheet(
            """
            background-color: #02070d;
            border: 1px solid #1c354a;
            color: #36516a;
            font-size: 18px;
            font-weight: 600;
            """
        )

        camera_layout.addWidget(
            self.camera_view,
            1,
            0
        )


        # =================================================
        # RADAR PANEL
        # =================================================

        radar_panel = self.make_panel(
            "ULTRASONIC / RADAR SCAN"
        )

        radar_layout = radar_panel.layout()

        self.radar_view = QLabel()

        self.radar_view.setAlignment(
            Qt.AlignCenter
        )

        self.radar_view.setMinimumSize(
            400,
            350
        )

        self.radar_view.setStyleSheet(
            """
            background-color: #02070d;
            border: 1px solid #1c354a;
            """
        )

        radar_layout.addWidget(
            self.radar_view,
            1,
            0
        )


        # =================================================
        # TELEMETRY PANEL
        # =================================================

        telemetry = self.make_panel(
            "SYSTEM TELEMETRY"
        )

        telemetry_layout = telemetry.layout()


        # -------------------------------------------------
        # Servo Angle
        # -------------------------------------------------

        angle_title = QLabel(
            "SERVO ANGLE"
        )

        angle_title.setStyleSheet(
            """
            color: #7f9bb5;
            font-size: 11px;
            """
        )

        telemetry_layout.addWidget(
            angle_title
        )

        self.angle_label = QLabel(
            "000°"
        )

        self.angle_label.setStyleSheet(
            """
            color: #8ff7ff;
            font-size: 34px;
            font-weight: 700;
            """
        )

        telemetry_layout.addWidget(
            self.angle_label
        )


        # -------------------------------------------------
        # Distance
        # -------------------------------------------------

        distance_title = QLabel(
            "DISTANCE"
        )

        distance_title.setStyleSheet(
            """
            color: #7f9bb5;
            font-size: 11px;
            """
        )

        telemetry_layout.addWidget(
            distance_title
        )

        self.distance_label = QLabel(
            "-- cm"
        )

        self.distance_label.setStyleSheet(
            """
            color: #8ff7ff;
            font-size: 30px;
            font-weight: 700;
            """
        )

        telemetry_layout.addWidget(
            self.distance_label
        )


        # -------------------------------------------------
        # Scanning
        # -------------------------------------------------

        scan_title = QLabel(
            "SCANNING STATUS"
        )

        scan_title.setStyleSheet(
            """
            color: #7f9bb5;
            font-size: 11px;
            """
        )

        telemetry_layout.addWidget(
            scan_title
        )

        self.scan_label = QLabel(
            "● ACTIVE"
        )

        self.scan_label.setStyleSheet(
            """
            color: #62ff8c;
            font-size: 18px;
            font-weight: 700;
            """
        )

        telemetry_layout.addWidget(
            self.scan_label
        )


        # -------------------------------------------------
        # Detection
        # -------------------------------------------------

        detection_title = QLabel(
            "AI DETECTION"
        )

        detection_title.setStyleSheet(
            """
            color: #7f9bb5;
            font-size: 11px;
            """
        )

        telemetry_layout.addWidget(
            detection_title
        )

        self.detection_label = QLabel(
            "CLEAR"
        )

        self.detection_label.setWordWrap(
            True
        )

        self.detection_label.setStyleSheet(
            """
            color: #62ff8c;
            font-size: 22px;
            font-weight: 700;
            """
        )

        telemetry_layout.addWidget(
            self.detection_label
        )


        # -------------------------------------------------
        # Connection
        # -------------------------------------------------

        self.connection_label = QLabel(
            "ESP32: CONNECTING..."
        )

        self.connection_label.setStyleSheet(
            """
            color: #7f9bb5;
            font-size: 11px;
            margin-top: 20px;
            """
        )

        telemetry_layout.addWidget(
            self.connection_label
        )


        self.camera_status_label = QLabel(
            "CAMERA: STARTING..."
        )

        self.camera_status_label.setStyleSheet(
            """
            color: #7f9bb5;
            font-size: 11px;
            """
        )

        telemetry_layout.addWidget(
            self.camera_status_label
        )




        # =================================================
        # ADD PANELS
        # =================================================

        main.addWidget(
            camera_panel,
            1,
            0,
            2,
            1
        )

        main.addWidget(
            radar_panel,
            1,
            1,
            2,
            1
        )

        main.addWidget(
            telemetry,
            1,
            2,
            2,
            1
        )


        # Column widths

        main.setColumnStretch(
            0,
            5
        )

        main.setColumnStretch(
            1,
            4
        )

        main.setColumnStretch(
            2,
            2
        )


    # =====================================================
    # MAKE PANEL
    # =====================================================

    def make_panel(
        self,
        title_text
    ):

        panel = QFrame()

        layout = QGridLayout(
            panel
        )

        layout.setContentsMargins(
            12,
            10,
            12,
            12
        )

        layout.setSpacing(
            8
        )


        title = QLabel(
            "●  " + title_text
        )

        title.setStyleSheet(
            """
            color: #ffffff;
            font-size: 12px;
            font-weight: 700;
            """
        )

        layout.addWidget(
            title,
            0,
            0
        )

        return panel


    # =====================================================
    # START THREADS
    # =====================================================

    def start_threads(self):

        self.serial_worker = SerialWorker()

        self.serial_worker.data_received.connect(
            self.receive_serial
        )

        self.serial_worker.connection_status.connect(
            self.update_connection
        )

        self.serial_worker.start()


        self.camera_worker = CameraWorker()

        self.camera_worker.frame_ready.connect(
            self.receive_camera
        )

        self.camera_worker.camera_status.connect(
            self.update_camera_status
        )

        self.camera_worker.start()


    # =====================================================
    # SERIAL DATA
    # =====================================================

    def receive_serial(
        self,
        angle,
        distance
    ):

        self.angle = angle
        self.distance = distance

        self.angle_label.setText(
            f"{angle:03d}°"
        )

        if distance >= 0:

            self.distance_label.setText(
                f"{distance} cm"
            )

        else:

            self.distance_label.setText(
                "-- cm"
            )


    # =====================================================
    # SERIAL STATUS
    # =====================================================

    def update_connection(
        self,
        status
    ):

        self.connection_label.setText(
            "ESP32: " + status
        )

        if "CONNECTED" in status:

            self.connection_label.setStyleSheet(
                """
                color: #62ff8c;
                font-size: 11px;
                margin-top: 20px;
                """
            )

        else:

            self.connection_label.setStyleSheet(
                """
                color: #ff6b6b;
                font-size: 11px;
                margin-top: 20px;
                """
            )


    # =====================================================
    # CAMERA FRAME
    # =====================================================

    def receive_camera(
        self,
        frame,
        objects
    ):

        self.objects = objects


        # -------------------------------------------------
        # Detection status
        # -------------------------------------------------

        if objects:

            names = sorted(
                set(
                    obj[0]
                    for obj in objects
                )
            )

            text = "\n".join(
                name.upper()
                for name in names
            )

            self.detection_label.setText(
                text
            )

            self.detection_label.setStyleSheet(
                """
                color: #ff6b6b;
                font-size: 20px;
                font-weight: 700;
                """
            )

        else:

            self.detection_label.setText(
                "CLEAR"
            )

            self.detection_label.setStyleSheet(
                """
                color: #62ff8c;
                font-size: 22px;
                font-weight: 700;
                """
            )


        # -------------------------------------------------
        # Convert OpenCV image to Qt
        # -------------------------------------------------

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        height, width, channel = rgb.shape

        bytes_per_line = (
            channel * width
        )

        image = QImage(
            rgb.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888
        )

        pixmap = QPixmap.fromImage(
            image
        )

        pixmap = pixmap.scaled(
            self.camera_view.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.camera_view.setPixmap(
            pixmap
        )

        
        # =====================================================
    # CAMERA STATUS
    # =====================================================

    def update_camera_status(
        self,
        status
    ):

        self.camera_status_label.setText(
            "CAMERA: " + status
        )

        if "ONLINE" in status:

            self.camera_status_label.setStyleSheet(
                """
                color: #62ff8c;
                font-size: 11px;
                """
            )

        else:

            self.camera_status_label.setStyleSheet(
                """
                color: #ff6b6b;
                font-size: 11px;
                """
            )


    # =====================================================
    # RADAR
    # =====================================================

    def update_radar(self):

        width = max(
            self.radar_view.width(),
            300
        )

        height = max(
            self.radar_view.height(),
            250
        )

        # -------------------------------------------------
        # Create black radar image
        # -------------------------------------------------

        radar = QImage(
            width,
            height,
            QImage.Format_RGB888
        )

        radar.fill(
            Qt.black
        )

        from PyQt5.QtGui import QPainter, QPen

        painter = QPainter(
            radar
        )

        # -------------------------------------------------
        # Radar styling
        # -------------------------------------------------

        pen = QPen(
            Qt.darkGreen
        )

        pen.setWidth(
            2
        )

        painter.setPen(
            pen
        )


        cx = width // 2

        cy = height - 25

        radius = min(
            width // 2 - 25,
            height - 45
        )


        # -------------------------------------------------
        # Radar arcs
        # -------------------------------------------------

        for r in [
            radius,
            int(radius * 0.66),
            int(radius * 0.33)
        ]:

            painter.drawArc(
                cx - r,
                cy - r,
                2 * r,
                2 * r,
                0,
                180 * 16
            )


        # -------------------------------------------------
        # Horizontal line
        # -------------------------------------------------

        painter.drawLine(
            cx - radius,
            cy,
            cx + radius,
            cy
        )


        # -------------------------------------------------
        # Scan angle
        # -------------------------------------------------

        angle = max(
            0,
            min(
                180,
                self.angle
            )
        )

        radians = math.radians(
            angle
        )

        x = int(
            cx + radius * math.cos(
                math.pi - radians
            )
        )

        y = int(
            cy - radius * math.sin(
                math.pi - radians
            )
        )

        pen2 = QPen(
            Qt.green
        )

        pen2.setWidth(
            4
        )

        painter.setPen(
            pen2
        )

        painter.drawLine(
            cx,
            cy,
            x,
            y
        )


        # -------------------------------------------------
        # Angle labels
        # -------------------------------------------------

        painter.setPen(
            Qt.white
        )

        painter.drawText(
            15,
            height - 8,
            "0°"
        )

        painter.drawText(
            cx - 12,
            20,
            "90°"
        )

        painter.drawText(
            width - 40,
            height - 8,
            "180°"
        )


        # -------------------------------------------------
        # Distance marker
        # -------------------------------------------------

        if self.distance > 0:

            d = min(
                self.distance,
                300
            )

            marker_radius = int(
                radius * d / 300
            )

            mx = int(
                cx + marker_radius *
                math.cos(
                    math.pi - radians
                )
            )

            my = int(
                cy - marker_radius *
                math.sin(
                    math.pi - radians
                )
            )

            painter.setPen(
                QPen(
                    Qt.red,
                    8
                )
            )

            painter.drawPoint(
                mx,
                my
            )


        painter.end()


        self.radar_view.setPixmap(
            QPixmap.fromImage(
                radar
            )
        )


    # =====================================================
    # CLOSE
    # =====================================================

    def closeEvent(
        self,
        event
    ):

        global serial_running
        global camera_running

        serial_running = False
        camera_running = False

        try:

            self.serial_worker.quit()

        except:
            pass

        try:

            self.camera_worker.quit()

        except:
            pass

        event.accept()


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    window = IndustrialGUI()

    window.show()

    sys.exit(
        app.exec_()
    )