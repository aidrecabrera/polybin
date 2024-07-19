import os
import sys
import threading
import time
import argparse
import logging
from collections import deque
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from lib.polybin import Polybin
from lib.dispose import Dispose
from lib.logger import Logger
from inference_sdk import InferenceHTTPClient
from inference import InferencePipeline
from inference.core.interfaces.stream.sinks import render_boxes

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

polybin = Polybin(port='/dev/ttyUSB0', socketio=socketio)
dispose = Dispose(32, 35)
logger = Logger(url, key)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Garbage Segregation System")
    parser.add_argument('--version', type=int, default=4, help="Model version number (default is 4)")
    parser.add_argument('--render_boxes', type=bool, default=False, help="Enable or disable rendering of boxes")
    parser.add_argument('--confidence', type=float, default=0.7, help="Confidence threshold for inference")
    return parser.parse_args()

args = parse_arguments()
model_id = f"garbage-segregator-ndyo4/{args.version}"

class DetectionState:
    def __init__(self, confirmation_time=2):
        self.reset()
        self.confirmation_time = confirmation_time
        self.lock = threading.Lock()
        logging.info(f"DetectionState initialized with confirmation time of {confirmation_time} seconds")

    def reset(self):
        self.current_detection = None
        self.detection_start_time = 0
        self.recent_detections = deque(maxlen=10)
        logging.info("Detection state reset")

    def update(self, detection):
        with self.lock:
            current_time = time.time()
            
            if detection != self.current_detection:
                logging.info(f"New detection: {detection}. Previous: {self.current_detection}")
                self.current_detection = detection
                self.detection_start_time = current_time
                self.recent_detections.clear()
            else:
                logging.debug(f"Consistent detection: {detection}")
            
            self.recent_detections.append((detection, current_time))
            logging.debug(f"Recent detections queue updated. Length: {len(self.recent_detections)}")

    def is_detection_confirmed(self):
        with self.lock:
            if not self.current_detection:
                logging.debug("No current detection to confirm")
                return False

            current_time = time.time()
            time_elapsed = current_time - self.detection_start_time
            
            logging.debug(f"Checking confirmation for {self.current_detection}. Time elapsed: {time_elapsed:.2f}s")
            
            if time_elapsed >= self.confirmation_time:
                recent_matching_detections = sum(1 for d, _ in self.recent_detections 
                                                 if d == self.current_detection)
                match_percentage = (recent_matching_detections / len(self.recent_detections)) * 100 if self.recent_detections else 0
                
                logging.debug(f"Recent matching detections: {recent_matching_detections}/{len(self.recent_detections)} ({match_percentage:.2f}%)")
                
                if match_percentage >= 80:
                    logging.info(f"Detection confirmed: {self.current_detection}")
                    return True
                else:
                    logging.info(f"Detection not confirmed. Insufficient matching percentage: {match_percentage:.2f}%")
            else:
                logging.debug(f"Not enough time elapsed for confirmation. Needed: {self.confirmation_time}s, Elapsed: {time_elapsed:.2f}s")
            
            return False

    def get_confirmed_detection(self):
        result = self.current_detection if self.is_detection_confirmed() else None
        logging.debug(f"get_confirmed_detection called. Result: {result}")
        return result

detection_state = DetectionState(confirmation_time=2)

def on_prediction(predictions, video_frame, render_boxes_enabled):
    """Handle predictions from the inference pipeline."""
    try:
        if render_boxes_enabled:
            render_boxes(predictions, video_frame)
        
        if 'image' in predictions and 'predictions' in predictions:
            if predictions['predictions']:
                for prediction in predictions['predictions']:
                    logger.log_prediction(prediction)
                
                object_class = predictions['predictions'][0]['class']
                confidence = predictions['predictions'][0]['confidence']
                
                logging.debug(f"Raw prediction: {object_class} (confidence: {confidence:.2f})")
                
                detection_state.update(object_class)
                confirmed_detection = detection_state.get_confirmed_detection()

                if confirmed_detection:
                    logging.info(f"Confirmed detection: {confirmed_detection} (confidence: {confidence:.2f})")

                    if dispose.can_perform_action():
                        if confirmed_detection == 'Recyclable':
                            dispose.dispose_recyclable()
                            status = 'Recyclable'
                        elif confirmed_detection == 'Bio-degradable':
                            dispose.dispose_biodegradable()
                            status = 'Biodegradable'
                        elif confirmed_detection == 'Non-biodegradable':
                            dispose.dispose_non_biodegradable()
                            status = 'Non-Biodegradable'
                        elif confirmed_detection == 'Hazardous':
                            dispose.dispose_hazardous()
                            status = 'Hazardous'
                        
                        logger.log_dispose({"bin_type": status})
                        logging.info(f"Action performed: {status}")
                        detection_state.reset()
                        logging.info("Detection state completely reset after disposal")
                    else:
                        logging.warning("Action prevented: Dispose cooldown in effect")
                else:
                    logging.debug(f"Detection not yet confirmed: {object_class}")
            else:
                logging.debug("No detection in this frame")
        else:
            logging.error("Invalid results format in predictions")
    except Exception as e:
        logging.error(f"Error in on_prediction: {e}", exc_info=True)

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