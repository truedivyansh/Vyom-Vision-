from ultralytics import YOLO
import cv2

model = YOLO("yolo11n.pt")

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera open nahi ho raha")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Camera frame nahi mil raha")
        break

    results = model(frame, conf=0.5)

    annotated_frame = results[0].plot()

    cv2.imshow("YOLO Live Detection", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()