import logging
from supabase import create_client, Client

class Logger:
    def __init__(self, url: str, key: str):
        self.supabase: Client = create_client(url, key)
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def log_prediction(self, prediction: dict):
        try:
            self.supabase.table("prediction_log").insert([prediction])
            logging.debug(f"Prediction logged: {prediction}")
        except Exception as e:
            logging.error(f"Failed to log prediction: {prediction} - Error: {e}")

    def log_dispose(self, dispose: dict):
        try:
            self.supabase.table("dispose_log").insert([dispose])
            logging.debug(f"Dispose logged: {dispose}")
        except Exception as e:
            logging.error(f"Failed to log dispose: {dispose} - Error: {e}")

    def log_bin_status(self, status: dict):
        try:
            self.supabase.table("bin_levels").insert([status])
            logging.debug(f"Bin status logged: {status}")
        except Exception as e:
            logging.error(f"Failed to log bin status: {status} - Error: {e}")

    def log_alert(self, alert: dict):
        try:
            self.supabase.table("alert_log").insert([alert])
            logging.debug(f"Alert logged: {alert}")
        except Exception as e:
            logging.error(f"Failed to log alert: {alert} - Error: {e}")
