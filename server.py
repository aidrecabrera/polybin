import os
import sys
import threading
import time
import argparse
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from lib.polybin import Polybin
from lib.dispose import Dispose
from inference_sdk import InferenceHTTPClient
from inference import InferencePipeline
from inference.core.interfaces.stream.sinks import render_boxes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

polybin = Polybin(port='/dev/ttyUSB0', socketio=socketio)
dispose = Dispose(32, 35)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Garbage Segregation System")
    parser.add_argument('--version', type=int, default=4, help="Model version number (default is 4)")
    parser.add_argument('--render_boxes', type=bool, default=False, help="Enable or disable rendering of boxes")
    parser.add_argument('--confidence', type=float, default=0.7, help="Confidence threshold for inference")
    return parser.parse_args()

args = parse_arguments()
model_id = f"garbage-segregator-ndyo4/{args.version}"

def on_prediction(predictions, video_frame, render_boxes_enabled):
    """Handle predictions from the inference pipeline."""
    try:
        if render_boxes_enabled:
            render_boxes(predictions, video_frame)
        
        if 'image' in predictions and 'predictions' in predictions:
            if predictions['predictions']:
                current_time = time.time()
                last_action_time = dispose.last_action_time
                cooldown_period = dispose.COOLDOWN_PERIOD
                if current_time - last_action_time >= cooldown_period:
                    object_class = predictions['predictions'][0]['class']
                    confidence = predictions['predictions'][0]['confidence']
                    logging.info(f"Detected object class: {object_class}")
                    logging.info(f"Confidence: {confidence}")

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
                    logging.info(f"Action performed: {status}")
                else:
                    logging.info("Action prevented: Cooldown in effect")
            else:
                logging.info("No detection or unable to perform action")
        else:
            logging.error("Invalid results format")
    except Exception as e:
        logging.error(f"Error in on_prediction: {e}")

def start_pipeline():
    """Start the inference pipeline."""
    try:
        pipeline = InferencePipeline.init(
            model_id=model_id, 
            video_reference=0, 
            on_prediction=lambda predictions, video_frame: on_prediction(predictions, video_frame, args.render_boxes),
            confidence=args.confidence
        )
        pipeline.start()
        pipeline.join()
    except Exception as e:
        logging.error(f"Error in start_pipeline: {e}")

def sensor_data_updater():
    """Continuously update sensor data."""
    try:
        while True:
            polybin.update_sensor_data()
    except Exception as e:
        logging.error(f"Error in sensor_data_updater: {e}")

@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    """Get the latest sensor data."""
    try:
        return jsonify(polybin.latest_data)
    except Exception as e:
        logging.error(f"Error in get_sensor_data: {e}")
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connections."""
    try:
        emit('sensor_update', polybin.latest_data)
    except Exception as e:
        logging.error(f"Error in handle_connect: {e}")

if __name__ == "__main__":
    try:
        detection_thread = threading.Thread(target=start_pipeline)
        detection_thread.daemon = True
        detection_thread.start()

        updater_thread = threading.Thread(target=sensor_data_updater)
        updater_thread.daemon = True
        updater_thread.start()

        socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
    except Exception as e:
        logging.error(f"Error in main: {e}")