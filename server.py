import time
import threading
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import serial
from config import (
    FLASK_DEBUG, FLASK_HOST, FLASK_PORT,
    SENSOR_SERIAL_PORT, NOTIFICATION_INTERVAL,
    SENSOR_UPDATE_INTERVAL, SENSOR_THRESHOLD
)
from lib.data import Data
from lib.sms import Sms

sms = Sms()
sensor = Data("/dev/ttyACM0")
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


latest_data = {
    "SENSOR_1": 40,
    "SENSOR_2": 40,
    "SENSOR_3": 40,
    "SENSOR_4": 40,
}

notification_sent = {
    "bio": False,
    "non": False,
    "rec": False,
    "haz": False
}

last_notification_time = time.time()

def sensor_data_refresh():
    while True:
        sensor_data_retrieve()
        time.sleep(SENSOR_UPDATE_INTERVAL)

def sensor_data_retrieve():
    global latest_data, sms, last_notification_time
    try:
        if sensor.check_transmission(serial_port=SENSOR_SERIAL_PORT):
            latest_data = {
                "SENSOR_1": sensor.sensors["SENSOR_1"],
                "SENSOR_2": sensor.sensors["SENSOR_2"],
                "SENSOR_3": sensor.sensors["SENSOR_3"],
                "SENSOR_4": sensor.sensors["SENSOR_4"],
            }
            print(latest_data)
            socketio.emit('sensor_update', latest_data)

            if time.time() - last_notification_time >= NOTIFICATION_INTERVAL:
                last_notification_time = time.time()
                for bin_type, sensor_value in latest_data.items():
                    check_and_notify(bin_type, sensor_value, SENSOR_THRESHOLD)
    except serial.SerialException:
        print("Serial connection issue.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        socketio.emit('sensor_update', latest_data)

def check_and_notify(bin_type, sensor_value, threshold):
    global notification_sent
    if sensor_value <= threshold and not notification_sent[bin_type]:
        sms.send_notification(bin_type)
        notification_sent[bin_type] = True
    elif sensor_value > threshold:
        notification_sent[bin_type] = False
    time.sleep(5)

@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    return jsonify(latest_data)

@socketio.on('connect')
def handle_connect():
    emit('sensor_update', latest_data)

if __name__ == "__main__":
    updater_thread = threading.Thread(target=sensor_data_refresh)
    updater_thread.daemon = True
    updater_thread.start()
    socketio.run(app, debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT, allow_unsafe_werkzeug=True)
