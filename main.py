import time
import threading
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from config import COOLDOWN_PERIOD
from lib.polybin import Polybin

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

polybin = Polybin()

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