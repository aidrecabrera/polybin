from flask import Flask, render_template, request, jsonify, Response
import RPi.GPIO as GPIO
import time
import threading
import cv2

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

def dispose_biodegradable():
    print("Performing action: Disposing Biodegradable")
    set_servo_angle(SERVO_PIN_1, 0)
    set_servo_angle(SERVO_PIN_2, 0)
    time.sleep(1)
    set_servo_angle(SERVO_PIN_2, 90)

def dispose_non_biodegradable():
    print("Performing action: Disposing Non-Biodegradable")
    set_servo_angle(SERVO_PIN_1, 90)
    set_servo_angle(SERVO_PIN_2, 0)
    time.sleep(1)
    set_servo_angle(SERVO_PIN_2, 90)

def dispose_recyclable():
    print("Performing action: Disposing Recyclable")
    set_servo_angle(SERVO_PIN_1, 0)
    set_servo_angle(SERVO_PIN_2, 180)
    time.sleep(1)
    set_servo_angle(SERVO_PIN_2, 90)

def dispose_dangerous():
    print("Performing action: Disposing Dangerous/Hazardous Waste")
    set_servo_angle(SERVO_PIN_1, 90)
    set_servo_angle(SERVO_PIN_2, 180)
    time.sleep(1)
    set_servo_angle(SERVO_PIN_2, 90)

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
        if action == 'BIO':
            dispose_biodegradable()
            status = 'Biodegradable'
        elif action == 'NON':
            dispose_non_biodegradable()
            status = 'Non-Biodegradable'
        elif action == 'REC':
            dispose_recyclable()
            status = 'Recyclable'
        elif action == 'HAZ':
            dispose_dangerous()
            status = 'Hazardous'
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
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5001)
    finally:
        camera.release()
        GPIO.cleanup()