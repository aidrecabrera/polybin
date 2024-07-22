from fileinput import filename
import logging
import threading
import queue
import time
from supabase import create_client, Client
import cv2

class AsyncLogger:
    def __init__(self, url: str, key: str):
        self.supabase: Client = create_client(url, key)
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def _worker(self):
        while True:
            try:
                table_name, data, log_type = self.queue.get()
                self._log(table_name, data, log_type)
            except Exception as e:
                logging.error(f"AsyncLogger worker error: {e}")
            finally:
                self.queue.task_done()

    def _log(self, table_name: str, data: dict, log_type: str):
        try:
            self.supabase.table(table_name).insert([data]).execute()
            logging.debug(f"{log_type.capitalize()} logged: {data}")
        except Exception as e:
            logging.error(f"Failed to log {log_type}: {data} - Error: {e}")

    def log(self, table_name: str, data: dict, log_type: str):
        self.queue.put((table_name, data, log_type))

    def log_prediction(self, prediction: dict):
        self.log("prediction_log", prediction, "prediction")

    def log_dispose(self, dispose: dict):
        self.log("dispose_log", dispose, "dispose")

    def log_bin_status(self, status: dict):
        self.log("bin_levels", status, "bin status")

    def log_alert(self, alert: dict):
        self.log("alert_log", alert, "alert")

    def log_dataset(self, frame_data: tuple, is_confirmed_detection: bool):
        logging.info("Logging dataset debug message.")
        if is_confirmed_detection:
            _, buffer = cv2.imencode('.jpg', frame_data[1])
            data = buffer.tobytes()
            bucket_name = "dataset/images"
            filename = f"{int(time.time())}.jpg"
            self.supabase.storage.from_(bucket_name).upload(filename, data)
