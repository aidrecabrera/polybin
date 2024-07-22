import logging
import threading
import queue
from supabase import create_client, Client
import io
import cv2
import numpy as np


class AsyncLogger:
    def __init__(self, url: str, key: str):
        self.supabase: Client = create_client(url, key)
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        self.lock = threading.Lock()
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
                
    def _execute_task(self, task):
        method, args, kwargs = task
        try:
            method(*args, **kwargs)
        except Exception as e:
            logging.error(f"Failed to execute task: {method.__name__} - Error: {e}")

    def _log(self, table_name: str, data: dict, log_type: str):
        try:
            with self.lock:
                self.supabase.table(table_name).insert([data]).execute()
            logging.debug(f"{log_type.capitalize()} logged: {data}")
        except Exception as e:
            logging.error(f"Failed to log {log_type}: {data} - Error: {e}")
            
    def _upload_file(self, file_data, path, content_type):
        try:
            with self.lock:
                self.supabase.storage.from_("dataset").upload(
                    file=file_data,
                    path=path,
                    file_options={"content-type": content_type}
                )
            logging.debug(f"File uploaded: {path}")
        except Exception as e:
            logging.error(f"Failed to upload file {path}: {e}")

    # TODO: review this change
    def log(self, table_name: str, data: dict, log_type: str):
        self.queue.put((self._log, (table_name, data, log_type), {}))

    def log_prediction(self, prediction: dict):
        self.log("prediction_log", prediction, "prediction")

    def log_dispose(self, dispose: dict):
        self.log("dispose_log", dispose, "dispose")

    def log_bin_status(self, status: dict):
        self.log("bin_levels", status, "bin status")

    def log_alert(self, alert: dict):
        self.log("alert_log", alert, "alert")   

    def log_dataset(self, image_data, filename):
        is_success, buffer = cv2.imencode(".jpg", image_data)
        if not is_success:
            raise ValueError("Failed to encode image")

        io_buf = io.BytesIO(buffer)
        path_on_supastorage = f"images/{filename}"
        
        self.queue.put((self._upload_file, (io_buf, path_on_supastorage, "image/jpeg"), {}))
