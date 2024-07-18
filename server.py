import os
import sys
import threading
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

def on_prediction(predictions, video_frame):
    render_boxes(predictions, video_frame)
    if 'image' in predictions and 'predictions' in predictions:
        if predictions['predictions'] and dispose.can_perform_action():
            object_class = predictions['predictions'][0]['class']
            confidence = predictions['predictions'][0]['confidence']
            print("Detected object class:", object_class)
            print("Confidence:", confidence)
            if object_class == 'Recyclable':
                print("Disposing recyclable object")
                dispose.dispose_recyclable()
            elif object_class == 'Bio-degradable':
                print("Disposing bio-degradable object")
                dispose.dispose_biodegradable()
            elif object_class == 'Non-biodegradable':
                print("Disposing non-biodegradable object")
                dispose.dispose_non_biodegradable()
            elif object_class == 'Hazardous':
                print("Disposing hazardous object")
                dispose.dispose_hazardous()
            else:
                print("Unknown object class:", object_class)
        else:
            print("No detection or unable to perform action")
    else:
        print("Invalid results format")
        
def start_pipeline():
    pipeline = InferencePipeline.init(
        model_id="garbage-segregator-ndyo4/5", 
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
