from flask import Flask, render_template, request, jsonify, Response
import RPi.GPIO as GPIO
import time
import threading
import cv2
import torch
import numpy as np

app = Flask(__name__)

SERVO_PIN_1 = 32
SERVO_PIN_2 = 35
COOLDOWN_PERIOD = 2

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(SERVO_PIN_1, GPIO.OUT)
GPIO.setup(SERVO_PIN_2, GPIO.OUT)

last_action_time = time.time()

servo_lock = threading.Lock()

camera = cv2.VideoCapture(0)

model = torch.hub.load('ultralytics/yolov5', 'custom', path='model/weights/best.pt')
class_names = ['Bio-degradable', 'Hazardous', 'Non-biodegradable', 'Recyclable']

def set_servo_angle(servo_pin, angle):
    with servo_lock:
        pwm = GPIO.PWM(servo_pin, 50)
        pwm.start(0)
        duty = angle / 18 + 2
        GPIO.output(servo_pin, GPIO.HIGH)
        pwm.ChangeDutyCycle(duty)
        time.sleep(1)
        GPIO.output(servo_pin, GPIO.LOW)
        pwm.ChangeDutyCycle(0)
        pwm.stop()

def dispose_waste(waste_type):
    print(f"Disposing {waste_type} waste")
    if waste_type == 'Bio-degradable':
        set_servo_angle(SERVO_PIN_1, 0)
        set_servo_angle(SERVO_PIN_2, 0)
    elif waste_type == 'Non-biodegradable':
        set_servo_angle(SERVO_PIN_1, 90)
        set_servo_angle(SERVO_PIN_2, 0)
    elif waste_type == 'Recyclable':
        set_servo_angle(SERVO_PIN_1, 0)
        set_servo_angle(SERVO_PIN_2, 180)
    elif waste_type == 'Hazardous':
        set_servo_angle(SERVO_PIN_1, 90)
        set_servo_angle(SERVO_PIN_2, 180)
    
    time.sleep(1)
    set_servo_angle(SERVO_PIN_2, 90)
    print(f"Finished disposing {waste_type} waste")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/control', methods=['POST'])
def control():
    global last_action_time
    data = request.get_json()
    action = data.get('action')
    status = 'unknown'
    current_time = time.time()

    if current_time - last_action_time >= COOLDOWN_PERIOD:
        if action in ['BIO', 'NON', 'REC', 'HAZ']:
            waste_type = class_names[['BIO', 'HAZ', 'NON', 'REC'].index(action)]
            dispose_waste(waste_type)
            status = waste_type
        last_action_time = current_time
        print(f"Action performed: {status}")
    else:
        status = 'Cooldown in effect'
        print("Action prevented: Cooldown in effect")

    return jsonify(status=status)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Perform object detection
            results = model(frame)
            
            # Draw bounding boxes and labels
            for det in results.xyxy[0]:
                x1, y1, x2, y2, conf, cls = det.tolist()
                label = f"{class_names[int(cls)]} {conf:.2f}"
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Automatically dispose of detected waste
            if len(results.xyxy[0]) > 0:
                best_det = results.xyxy[0][0]  # Get the first detection (assuming it's the most prominent)
                waste_type = class_names[int(best_det[5])]
                print(f"Detected {waste_type} waste")
                dispose_waste(waste_type)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    try:
        print("Starting ML-integrated Waste Sorter")
        app.run(host='0.0.0.0', port=5001)
    finally:
        print("Shutting down ML-integrated Waste Sorter")
        camera.release()
        GPIO.cleanup()