import os
import sys
import cv2
import threading
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from lib.polybin import Polybin
from lib.dispose import Dispose
from inference_sdk import InferenceHTTPClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
polybin = Polybin(port='/dev/ttyUSB0', socketio=socketio)
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="MKTjsmucOSIZyKIaoQU7"
)

def capture_frame():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return None
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Error: Could not read frame.")
        return None
    return frame

def process_frame(frame):
    if frame is None:
        return None
    cv2.imwrite("temp_frame.jpg", frame)
    return CLIENT.infer("temp_frame.jpg", model_id="garbage-segregator-ndyo4/5")

def process_inference():
    dispose = Dispose(32, 35)
    frame = capture_frame()
    result = process_frame(frame)
    
    if result is not None and 'objects' in result and result['objects'] and dispose.can_perform_action():
        object_class = result['objects'][0]['class']
        if object_class == 'recyclable':
            dispose.open_recyclable()
        elif object_class == 'biodegradable':
            dispose.open_non_recyclable()
        elif object_class == 'non-biodegradable':
            dispose.open_organic()
        elif object_class == 'hazardous':
            dispose.open_hazardous()
        else:
            print("Unknown object class:", object_class)
    else:
        print("No detection or unable to perform action")

def capture_and_process():
    while True:
        process_inference()

def sensor_data_updater():
    while True:
        polybin.update_sensor_data()

@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    return jsonify(polybin.latest_data)

@socketio.on('connect')
def handle_connect():
    emit('sensor_update', polybin.latest_data)

if __name__ == "__main__":
    capture_thread = threading.Thread(target=capture_and_process)
    capture_thread.daemon = True
    capture_thread.start()

    updater_thread = threading.Thread(target=sensor_data_updater)
    updater_thread.daemon = True
    updater_thread.start()

    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)