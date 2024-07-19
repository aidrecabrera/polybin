from supabase import create_client, Client

class Logger:
    def __init__(self, url: str, key: str):
        self.supabase: Client = create_client(url, key)

    def log_prediction(self, prediction: dict):
        self.supabase.table("prediction_log").insert([prediction])

    def log_dispose(self, dispose: dict):
        self.supabase.table("dispose_log").insert([dispose])

    def log_bin_status(self, status: dict):
        self.supabase.table("bin_levels").insert([status])

    def log_alert(self, alert: dict):
        self.supabase.table("alert_log").insert([alert])