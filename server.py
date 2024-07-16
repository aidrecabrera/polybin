import os
import sys
import threading
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.polybin import Polybin

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

polybin = Polybin(port='/dev/ttyUSB0', socketio=socketio)

@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    return jsonify(polybin.latest_data)

@socketio.on('connect')
def handle_connect():
    emit('sensor_update', polybin.latest_data)

def sensor_data_updater():
    while True:
        polybin.update_sensor_data()

if __name__ == "__main__":
    updater_thread = threading.Thread(target=sensor_data_updater)
    updater_thread.daemon = True
    updater_thread.start()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)