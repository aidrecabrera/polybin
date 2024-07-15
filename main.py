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

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class PolybinSystem:
    def __init__(self):
        # initialize variables
        self.last_action_time = time.time()
        self.last_notification_time = time.time()
        self.camera = cv2.VideoCapture(0)
        self.sensor_data = Data(SERIAL_PORT)
        self.sms_notifier = Sms(GSM_PORT)
        self.servo_controller = Servo(SERVO_PIN_1, SERVO_PIN_2)
        self.notification_sent = {bin_type: False for bin_type in ["bio", "non", "rec", "haz"]}

    def dispose_waste(self, waste_type):
        """handle waste disposal for different types"""
        actions = {
            'BIO': (0, 0, 90, "Biodegradable"),
            'NON': (90, 0, 90, "Non-Biodegradable"),
            'REC': (0, 180, 90, "Recyclable"),
            'HAZ': (90, 180, 90, "Dangerous/Hazardous")
        }
        
        if waste_type in actions:
            # perform actions for the specified waste type
            angle1, angle2, final_angle, description = actions[waste_type]
            print(f"disposing {description}")
            self.servo_controller.set_angle(SERVO_PIN_1, angle1)
            self.servo_controller.set_angle(SERVO_PIN_2, angle2)
            time.sleep(1)
            self.servo_controller.set_angle(SERVO_PIN_2, final_angle)
            return description
        return "Unknown"

    def update_sensor_data(self):
        """update sensor data and send notifications if needed"""
        if self.sensor_data.update():
            socketio.emit('sensor_update', self.sensor_data.sensors)
            
            current_time = time.time()
            if current_time - self.last_notification_time >= NOTIFICATION_INTERVAL:
                self.last_notification_time = current_time 
                for bin_type, sensor_value in zip(["bio", "non", "rec", "haz"], self.sensor_data.sensors.values()):
                    self.check_and_notify(bin_type, sensor_value)

    def check_and_notify(self, bin_type, sensor_value):
        """check sensor value and send notification if needed"""
        if sensor_value <= SENSOR_THRESHOLD and not self.notification_sent[bin_type]:
            self.sms_notifier.send_notification(bin_type)
            self.notification_sent[bin_type] = True 
        elif sensor_value > SENSOR_THRESHOLD:
            self.notification_sent[bin_type] = False

    def generate_frames(self):
        """generate video frames for streaming"""
        while True:
            success, frame = self.camera.read()
            if not success:
                break
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def cleanup(self):
        """release all resources"""
        self.camera.release()
        self.servo_controller.cleanup()

polybin = PolybinSystem()

@app.route('/')
def index():
    """render the main page"""
    return render_template('index.html')

@app.route('/control', methods=['POST'])
def control():
    """
    handle waste disposal control
    
    POST data:
    {
        "action": "BIO" | "NON" | "REC" | "HAZ"
    }
    
    Returns:
    {
        "status": "Biodegradable" | "Non-Biodegradable" | "Recyclable" | "Dangerous/Hazardous" | "Unknown" | "cooldown in effect"
    }
    """
    data = request.get_json()
    action = data.get('action')
    current_time = time.time()

    if current_time - polybin.last_action_time >= COOLDOWN_PERIOD:
        status = polybin.dispose_waste(action)
        polybin.last_action_time = current_time
        print(f"action performed: {status}")
    else:
        status = 'cooldown in effect'
        print("action prevented: cooldown in effect")

    return jsonify(status=status)

@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    """
    return the latest sensor data
    
    Returns:
    {
        "SENSOR_1": float,
        "SENSOR_2": float,
        "SENSOR_3": float,
        "SENSOR_4": float
    }
    """
    return jsonify(polybin.sensor_data.sensors)

@app.route('/video_feed')
def video_feed():
    """stream video feed"""
    return Response(polybin.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def handle_connect():
    """handle new socket connection"""
    emit('sensor_update', polybin.sensor_data.sensors)

def sensor_data_updater():
    """continuously update sensor data"""
    while True:
        polybin.update_sensor_data()
        time.sleep(2)

if __name__ == "__main__":
    try:
        # start sensor data updater thread
        updater_thread = threading.Thread(target=sensor_data_updater)
        updater_thread.daemon = True
        updater_thread.start()

        # run the flask app
        socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
    finally:
        # cleanup resources
        polybin.cleanup()
