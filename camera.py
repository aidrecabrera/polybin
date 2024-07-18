import cv2
import time
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

camera_index = 0
cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    logging.error(f"Error: Could not open camera with index {camera_index}")
    exit()

logging.info(f"Successfully opened camera with index {camera_index}")

fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
if cap.set(cv2.CAP_PROP_FOURCC, fourcc):
    logging.info("Successfully set fourcc to MJPG")
else:
    logging.warning("Failed to set fourcc to MJPG")

if cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640):
    logging.info("Successfully set frame width to 640")
else:
    logging.warning("Failed to set frame width to 640")

if cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480):
    logging.info("Successfully set frame height to 480")
else:
    logging.warning("Failed to set frame height to 480")

cv2.namedWindow("Live Preview", cv2.WINDOW_NORMAL)

frame_count = 0
start_time = time.time()

while True:

    ret, frame = cap.read()

    if not ret:
        logging.error("Failed to grab frame")

        cap.release()
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            logging.error("Failed to re-open camera. Exiting.")
            break
        continue

    frame_count += 1
    elapsed_time = time.time() - start_time
    fps = frame_count / elapsed_time
    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Live Preview", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

logging.info("Script finished executing")