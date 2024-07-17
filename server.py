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
cap = cv2.VideoCapture(0)
socketio = SocketIO(app, cors_allowed_origins="*")
polybin = Polybin(port='/dev/ttyUSB0', socketio=socketio)
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="MKTjsmucOSIZyKIaoQU7"
)

def capture_video():
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        exit()
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break
        cv2.imwrite("temp_frame.jpg", frame)
        result = CLIENT.infer("temp_frame.jpg", model_id="garbage-segregator-ndyo4/5")
    cap.release()
    cv2.destroyAllWindows()
    return result

def process_inference():
    dispose = Dispose(32, 35)
    result = capture_video()
    if result is not None and dispose.can_perform_action():
        if result['objects'][0]['class'] == 'recyclable':
           dispose.open_recyclable()
           return
        elif result['objects'][0]['class'] == 'biodegradable':
            dispose.open_non_recyclable()
            return
        elif result['objects'][0]['class'] == 'non-biodegradable':
            dispose.open_organic()
            return
        elif result['objects'][0]['class'] == 'hazardous':
            dispose.open_hazardous()
            return
        else:
            print("No Detection")
            return

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
    capture_thread = threading.Thread(target=capture_video)
    capture_thread.daemon = True
    capture_thread.start()
    updater_thread = threading.Thread(target=sensor_data_updater)
    updater_thread.daemon = True
    updater_thread.start()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)