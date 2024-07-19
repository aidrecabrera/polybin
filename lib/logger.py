import logging
from supabase import create_client, Client

class Logger:
    def __init__(self, url: str, key: str):
        self.supabase: Client = create_client(url, key)
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def log(self, table_name: str, data: dict, log_type: str) -> bool:
        try:
            self.supabase.table(table_name).insert([data]).execute()
            logging.debug(f"{log_type.capitalize()} logged: {data}")
            return True
        except Exception as e:
            logging.error(f"Failed to log {log_type}: {data} - Error: {e}")
            return False

    def log_prediction(self, prediction: dict) -> bool:
        return self.log("prediction_log", prediction, "prediction")

    def log_dispose(self, dispose: dict) -> bool:
        return self.log("dispose_log", dispose, "dispose")

    def log_bin_status(self, status: dict) -> bool:
        return self.log("bin_levels", status, "bin status")

    def log_alert(self, alert: dict) -> bool:
        return self.log("alert_log", alert, "alert")
