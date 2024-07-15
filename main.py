import time
import threading
import cv2
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from config import SERIAL_PORT, GSM_PORT, SERVO_PIN_1, SERVO_PIN_2, SENSOR_THRESHOLD, NOTIFICATION_INTERVAL, COOLDOWN_PERIOD
from lib.data import Data
from lib.sms import Sms
from lib.hardware import Servo
from lib.detect import Detect

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class PolybinSystem:
    def __init__(self):
        self.last_action_time = time.time()
        self.last_notification_time = time.time()
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.sensor_data = Data(SERIAL_PORT)
        self.sms_notifier = Sms(GSM_PORT)
        self.servo_controller = Servo(SERVO_PIN_1, SERVO_PIN_2)
        self.notification_sent = {bin_type: False for bin_type in ["bio", "non", "rec", "haz"]}
        self.frame = None
        self.frame_lock = threading.Lock()
        self.detector = Detect(model_path='model/weights/best.pt', img_size=320)
        self.detector.load_model()

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
            socketio.emit('sensor_update', self.sensor_data.sensors)
            
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

polybin = PolybinSystem()

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