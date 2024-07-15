import os
import sys
import time
import threading
import cv2
import serial
import RPi.GPIO as GPIO
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from data.sensor_data import HCSR04
from gsm.sms import BinNotificationSystem

# add parent directory to sys.path for imports

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# constants

SERVO_PIN_1 = 32
SERVO_PIN_2 = 35
COOLDOWN_PERIOD = 2
NOTIFICATION_INTERVAL = 10
SENSOR_THRESHOLD = 13
SERIAL_PORT = "/dev/ttyACM0"
GSM_PORT = "/dev/ttyUSB0"

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


class SmartBinSystem:
    def __init__(self):
        self.last_action_time = time.time()
        self.last_notification_time = time.time()
        self.servo_lock = threading.Lock()
        self.camera = cv2.VideoCapture(0)
        self.bin_system = BinNotificationSystem(port=GSM_PORT)
        self.latest_data = {f"SENSOR_{i}": 40 for i in range(1, 5)}
        self.notification_sent = {
            bin_type: False for bin_type in ["bio", "non", "rec", "haz"]
        }

        self._setup_gpio()

    def _setup_gpio(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        for pin in (SERVO_PIN_1, SERVO_PIN_2):
            GPIO.setup(pin, GPIO.OUT)

    def set_servo_angle(self, servo_pin, angle):
        with self.servo_lock:
            pwm = GPIO.PWM(servo_pin, 50)
            pwm.start(0)
            duty = angle / 18 + 2
            GPIO.output(servo_pin, GPIO.HIGH)
            pwm.ChangeDutyCycle(duty)
            time.sleep(1)
            GPIO.output(servo_pin, GPIO.LOW)
            pwm.ChangeDutyCycle(0)
            pwm.stop()

    def dispose_waste(self, waste_type):
        actions = {
            "BIO": (0, 0, 90, "Biodegradable"),
            "NON": (90, 0, 90, "Non-Biodegradable"),
            "REC": (0, 180, 90, "Recyclable"),
            "HAZ": (90, 180, 90, "Dangerous/Hazardous"),
        }

        if waste_type in actions:
            angle1, angle2, final_angle, description = actions[waste_type]
            print(f"disposing {description}")
            self.set_servo_angle(SERVO_PIN_1, angle1)
            self.set_servo_angle(SERVO_PIN_2, angle2)
            time.sleep(1)
            self.set_servo_angle(SERVO_PIN_2, final_angle)
            return description
        return "Unknown"

    def update_sensor_data(self):
        sensor = HCSR04()
        try:
            if sensor.check_transmission(serial_port=SERIAL_PORT):
                sensor.get_bin_data()
                self.latest_data = {
                    f"SENSOR_{i}": getattr(sensor, f"sensor_{i}") for i in range(1, 5)
                }
                socketio.emit("sensor_update", self.latest_data)

                current_time = time.time()
                if current_time - self.last_notification_time >= NOTIFICATION_INTERVAL:
                    self.last_notification_time = current_time
                    for bin_type, sensor_value in zip(
                        ["bio", "non", "rec", "haz"], self.latest_data.values()
                    ):
                        self.check_and_notify(bin_type, sensor_value)
        except serial.SerialException:
            print("serial connection issue")
        except Exception as e:
            print(f"error: {e}")
        finally:
            socketio.emit("sensor_update", self.latest_data)

    def check_and_notify(self, bin_type, sensor_value):
        if sensor_value <= SENSOR_THRESHOLD and not self.notification_sent[bin_type]:
            self.bin_system.send_notification(bin_type)
            self.notification_sent[bin_type] = True
        elif sensor_value > SENSOR_THRESHOLD:
            self.notification_sent[bin_type] = False

    def generate_frames(self):
        while True:
            success, frame = self.camera.read()
            if not success:
                break
            ret, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

    def cleanup(self):
        self.camera.release()
        GPIO.cleanup()


smart_bin = SmartBinSystem()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/control", methods=["POST"])
def control():
    data = request.get_json()
    action = data.get("action")
    current_time = time.time()

    if current_time - smart_bin.last_action_time >= COOLDOWN_PERIOD:
        status = smart_bin.dispose_waste(action)
        smart_bin.last_action_time = current_time
        print(f"action performed: {status}")
    else:
        status = "cooldown in effect"
        print("action prevented: cooldown in effect")
    return jsonify(status=status)


@app.route("/sensor_data", methods=["GET"])
def get_sensor_data():
    return jsonify(smart_bin.latest_data)


@app.route("/video_feed")
def video_feed():
    return Response(
        smart_bin.generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@socketio.on("connect")
def handle_connect():
    emit("sensor_update", smart_bin.latest_data)


def sensor_data_updater():
    while True:
        smart_bin.update_sensor_data()
        time.sleep(2)


if __name__ == "__main__":
    try:
        updater_thread = threading.Thread(target=sensor_data_updater)
        updater_thread.daemon = True
        updater_thread.start()

        socketio.run(
            app, debug=True, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True
        )
    finally:
        smart_bin.cleanup()
