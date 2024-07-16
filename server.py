import os
import sys
import serial
import threading
import time

from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from lib.data import HCSR04
from lib.sms import BinNotificationSystem

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

bin_system = BinNotificationSystem(port='/dev/ttyUSB0')

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
    global latest_data, bin_system, last_notification_time
    sensor = HCSR04()
    try:
        if sensor.check_transmission(serial_port='/dev/ttyACM0'):
            sensor.get_bin_data()
            latest_data = {
                "SENSOR_1": sensor.sensor_1,
                "SENSOR_2": sensor.sensor_2,
                "SENSOR_3": sensor.sensor_3,
                "SENSOR_4": sensor.sensor_4
            }
            socketio.emit('sensor_update', latest_data)
           
            if time.time() - last_notification_time >= 10:
                last_notification_time = time.time() 
                check_and_notify("bio", sensor.sensor_1, 13)
                check_and_notify("non", sensor.sensor_2, 13)
                check_and_notify("rec", sensor.sensor_3, 13)
                check_and_notify("haz", sensor.sensor_4, 13)
    except serial.SerialException:
        print("Serial connection issue.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        socketio.emit('sensor_update', latest_data)

def check_and_notify(bin_type, sensor_value, threshold):
    global notification_sent
    if sensor_value <= threshold and not notification_sent[bin_type]:
        bin_system.send_notification(bin_type)
        notification_sent[bin_type] = True 
    elif sensor_value > threshold:
        notification_sent[bin_type] = False
    time.sleep(5)

def sensor_data_updater():
    while True:
        update_sensor_data()
        time.sleep(2)

if __name__ == "__main__":
    updater_thread = threading.Thread(target=sensor_data_updater)
    updater_thread.daemon = True
    updater_thread.start()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)