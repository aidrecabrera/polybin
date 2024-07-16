import time
import threading
import cv2
import serial
import serial.tools.list_ports
import requests
import numpy as np
from PIL import Image
import io
import RPi.GPIO as GPIO
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit

SERIAL_PORT = "/dev/ttyACM0"
GSM_PORT = "/dev/ttyUSB0"
SERVO_PIN_1 = 32
SERVO_PIN_2 = 35
SENSOR_THRESHOLD = 20
NOTIFICATION_INTERVAL = 3600
COOLDOWN_PERIOD = 5

class Servo:
    def __init__(self, pin1, pin2):
        self.pin1 = pin1
        self.pin2 = pin2
        self.lock = threading.Lock()
        self._setup_gpio()

    def _setup_gpio(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        for pin in (self.pin1, self.pin2):
            GPIO.setup(pin, GPIO.OUT)

    def set_angle(self, pin, angle):
        with self.lock:
            pwm = GPIO.PWM(pin, 50)
            pwm.start(0)
            duty = angle / 18 + 2
            GPIO.output(pin, GPIO.HIGH)
            pwm.ChangeDutyCycle(duty)
            time.sleep(1)
            GPIO.output(pin, GPIO.LOW)
            pwm.ChangeDutyCycle(0)
            pwm.stop()

    def cleanup(self):
        GPIO.cleanup()

class Sms:
    def __init__(self, port, baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate

    def send_notification(self, bin_type):
        commands = {'bio': 'a', 'non': 'b', 'rec': 'c', 'haz': 'd'}
        
        if bin_type not in commands:
            print(f"Invalid bin type: {bin_type}")
            return False

        try:
            with serial.Serial(self.port, self.baud_rate, timeout=1) as ser:
                time.sleep(2)
                ser.write(commands[bin_type].encode())
                print(f"Notification sent for {bin_type} bin")
            return True
        except serial.SerialException as e:
            print(f"SMS error: {e}")
            return False

class Data:
    def __init__(self, serial_port):
        self.serial_port = serial_port
        self.sensors = {f"SENSOR_{i}": 40 for i in range(1, 5)}

    def update(self):
        if not self.check_transmission():
            return False

        try:
            with serial.Serial(self.serial_port, 19200, timeout=1) as ser:
                ser.flush()
                ser.write(b'R')
                time.sleep(0.1)

                encoded_message = ser.read(20)
                if encoded_message:
                    for i in range(4):
                        sensor_value = int.from_bytes(encoded_message[i*4:(i+1)*4], 'little')
                        self.sensors[f"SENSOR_{i+1}"] = sensor_value
                    print(f"Updated sensor data: {self.sensors}")
                else:
                    print("No data received from sensors.")
            return True
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            return False

    def check_transmission(self):
        return self.serial_port in [port.device for port in serial.tools.list_ports.comports()]

class Detect:
    def __init__(self, api_key, model_id, confidence_threshold=0.287):
        self.api_key = api_key
        self.model_id = model_id
        self.confidence_threshold = confidence_threshold
        self.api_url = f"https://detect.roboflow.com/{model_id}"
        self.class_names = ['Bio-degradable', 'Hazardous', 'Non-biodegradable', 'Recyclable']

    def perform_inference(self, image):
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        elif isinstance(image, str):
            image = Image.open(image)
        elif not isinstance(image, Image.Image):
            raise ValueError("Input must be a NumPy array, PIL Image, or a string path to an image.")

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        response = requests.post(
            self.api_url,
            data=img_byte_arr,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"API_KEY {self.api_key}"
            },
            params={
                "confidence": self.confidence_threshold,
                "overlap": 30,
                "format": "json"
            }
        )

        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

        result = response.json()

        detections = []
        for prediction in result.get('predictions', []):
            x, y, width, height = prediction['x'], prediction['y'], prediction['width'], prediction['height']
            x1, y1 = x - width / 2, y - height / 2
            x2, y2 = x + width / 2, y + height / 2
            
            detections.append({
                'bounding_box': (x1, y1, x2, y2),
                'confidence': prediction['confidence'],
                'class': prediction['class']
            })

        return detections

class Polybin:
    def __init__(self, socketio):
        self.last_action_time = time.time()
        self.last_notification_time = time.time()
        self.socketio = socketio
        
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.sensor_data = Data(SERIAL_PORT)
        self.sms_notifier = Sms(GSM_PORT)
        self.servo_controller = Servo(SERVO_PIN_1, SERVO_PIN_2)
        self.notification_sent = {bin_type: False for bin_type in ["bio", "non", "rec", "haz"]}
        self.frame = None
        self.frame_lock = threading.Lock()
        self.detector = Detect(
            api_key="MKTjsmucOSIZyKIaoQU7",
            model_id="garbage-segregator-ndyo4/5",
            confidence_threshold=0.287
        )

    def dispose_waste(self, waste_type):
        actions = {
            'Bio-degradable': (0, 0, 90, "Biodegradable"),
            'Non-biodegradable': (90, 0, 90, "Non-Biodegradable"),
            'Recyclable': (0, 180, 90, "Recyclable"),
            'Hazardous': (90, 180, 90, "Dangerous/Hazardous")
        }
        
        if waste_type in actions:
            angle1, angle2, final_angle, description = actions[waste_type]
            print(f"Disposing {description}")
            self.servo_controller.set_angle(SERVO_PIN_1, angle1)
            self.servo_controller.set_angle(SERVO_PIN_2, angle2)
            time.sleep(1)
            self.servo_controller.set_angle(SERVO_PIN_2, final_angle)
            return description
        return "Unknown"

    def update_sensor_data(self):
        if self.sensor_data.update():
            self.socketio.emit('sensor_update', self.sensor_data.sensors)
            
            current_time = time.time()
            if current_time - self.last_notification_time >= NOTIFICATION_INTERVAL:
                self.last_notification_time = current_time 
                for bin_type, sensor_value in zip(["bio", "non", "rec", "haz"], self.sensor_data.sensors.values()):
                    self.check_and_notify(bin_type, sensor_value)

    def check_and_notify(self, bin_type, sensor_value):
        if sensor_value <= SENSOR_THRESHOLD and not self.notification_sent[bin_type]:
            self.sms_notifier.send_notification(bin_type)
            self.notification_sent[bin_type] = True 
        elif sensor_value > SENSOR_THRESHOLD:
            self.notification_sent[bin_type] = False

    def capture_frames(self):
        while True:
            success, frame = self.camera.read()
            if success:
                with self.frame_lock:
                    self.frame = frame
            time.sleep(0.033)

    def perform_detection(self, frame):
        detections = self.detector.perform_inference(frame)
        return detections

    def draw_detections(self, frame, detections):
        for detection in detections:
            bbox = detection['bounding_box']
            conf = detection['confidence']
            cls = detection['class']
            
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{cls}: {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        return frame

    def generate_frames(self):
        while True:
            with self.frame_lock:
                if self.frame is None:
                    continue
                frame = self.frame.copy()
            
            detections = self.perform_detection(frame)
            frame_with_detections = self.draw_detections(frame, detections)
            
            ret, buffer = cv2.imencode('.jpg', frame_with_detections, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def cleanup(self):
        self.camera.release()
        self.servo_controller.cleanup()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

polybin = Polybin(socketio)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/control', methods=['POST'])
def control():
    data = request.get_json()
    action = data.get('action')
    current_time = time.time()

    if current_time - polybin.last_action_time >= COOLDOWN_PERIOD:
        status = polybin.dispose_waste(action)
        polybin.last_action_time = current_time
        print(f"Action performed: {status}")
    else:
        status = 'Cooldown in effect'
        print("Action prevented: Cooldown in effect")

    return jsonify(status=status)

@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    return jsonify(polybin.sensor_data.sensors)

@app.route('/video_feed')
def video_feed():
    return Response(polybin.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def handle_connect():
    emit('sensor_update', polybin.sensor_data.sensors)

def sensor_data_updater():
    while True:
        polybin.update_sensor_data()
        time.sleep(2)

if __name__ == "__main__":
    try:
        updater_thread = threading.Thread(target=sensor_data_updater)
        updater_thread.daemon = True
        updater_thread.start()

        capture_thread = threading.Thread(target=polybin.capture_frames)
        capture_thread.daemon = True
        capture_thread.start()

        socketio.run(app, debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    finally:
        polybin.cleanup()