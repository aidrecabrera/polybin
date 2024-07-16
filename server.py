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

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

sms = Sms()

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

@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    return jsonify(latest_data)

@socketio.on('connect')
def handle_connect():
    emit('sensor_update', latest_data)

def update_sensor_data():
    global latest_data, sms, last_notification_time
    sensor = Data()
    try:
        if sensor.check_transmission(serial_port=SENSOR_SERIAL_PORT):
            sensor.get_bin_data(SENSOR_SERIAL_PORT)
            latest_data = {
                "SENSOR_1": sensor.sensor_1,
                "SENSOR_2": sensor.sensor_2,
                "SENSOR_3": sensor.sensor_3,
                "SENSOR_4": sensor.sensor_4
            }
            socketio.emit('sensor_update', latest_data)

            if time.time() - last_notification_time >= NOTIFICATION_INTERVAL:
                last_notification_time = time.time()
                check_and_notify("bio", sensor.sensor_1, SENSOR_THRESHOLD)
                check_and_notify("non", sensor.sensor_2, SENSOR_THRESHOLD)
                check_and_notify("rec", sensor.sensor_3, SENSOR_THRESHOLD)
                check_and_notify("haz", sensor.sensor_4, SENSOR_THRESHOLD)
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

def sensor_data_updater():
    while True:
        update_sensor_data()
        time.sleep(SENSOR_UPDATE_INTERVAL)

if __name__ == "__main__":
    updater_thread = threading.Thread(target=sensor_data_updater)
    updater_thread.daemon = True
    updater_thread.start()
    socketio.run(app, debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT, allow_unsafe_werkzeug=True)
