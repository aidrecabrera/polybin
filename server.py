import os
import sys
import threading
import time
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from lib.polybin import Polybin
from lib.dispose import Dispose
from inference_sdk import InferenceHTTPClient
from inference import InferencePipeline
from inference.core.interfaces.stream.sinks import render_boxes

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
polybin = Polybin(port='/dev/ttyUSB0', socketio=socketio)

dispose = Dispose(32, 35)

def on_prediction(predictions, video_frame, dispose):
    render_boxes(predictions, video_frame)
    if 'image' in predictions and 'predictions' in predictions:
        if predictions['predictions']:
            current_time = time.time()
            last_action_time = dispose.last_action_time
            cooldown_period = dispose.COOLDOWN_PERIOD
            if current_time - last_action_time >= cooldown_period:
                object_class = predictions['predictions'][0]['class']
                confidence = predictions['predictions'][0]['confidence']
                print("Detected object class:", object_class)
                print("Confidence:", confidence)
                if object_class == 'Recyclable':
                    dispose.dispose_recyclable()
                    status = 'Recyclable'
                elif object_class == 'Bio-degradable':
                    dispose.dispose_biodegradable()
                    status = 'Biodegradable'
                elif object_class == 'Non-biodegradable':
                    dispose.dispose_non_biodegradable()
                    status = 'Non-Biodegradable'
                elif object_class == 'Hazardous':
                    dispose.dispose_hazardous()
                    status = 'Hazardous'
                dispose.last_action_time = current_time
                print(f"Action performed: {status}")
            else:
                print("Action prevented: Cooldown in effect")
        else:
            print("No detection or unable to perform action")
    else:
        print("Invalid results format")

        
def start_pipeline():
    pipeline = InferencePipeline.init(
        model_id="garbage-segregator-ndyo4/4", 
        video_reference=0, 
        on_prediction=on_prediction,
        confidence=0.7
    )
    pipeline.start()
    pipeline.join()

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
    detection_thread = threading.Thread(target=start_pipeline)
    detection_thread.daemon = True
    detection_thread.start()

    updater_thread = threading.Thread(target=sensor_data_updater)
    updater_thread.daemon = True
    updater_thread.start()

    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
