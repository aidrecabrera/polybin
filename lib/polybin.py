import time
import serial
from alerts.alert import Alert
from lib.data import Data
from lib.sms import Sms
from lib.async_logger import AsyncLogger
from flask_socketio import SocketIO

class Polybin:
    def __init__(self, port, socketio: SocketIO, logger: AsyncLogger):
        self.bin_system = Sms(port=port)
        self.socketio = socketio
        self.logger = logger
        self.latest_data = {
            "SENSOR_1": 40,  # Biodegradable
            "SENSOR_2": 40,  # Non-biodegradable
            "SENSOR_3": 40,  # Recyclable
            "SENSOR_4": 40,  # Hazardous
        }
        self.notification_sent = {
            "bio": False,
            "non": False,
            "rec": False,
            "haz": False,
        }
        self.last_notification_time = time.time()
        self.alert = Alert()

    def update_sensor_data(self):
        sensor = Data()
        try:
            if sensor.check_transmission():
                sensor.retrieve_data()
                self.latest_data = {
                    "SENSOR_1": sensor.sensor_1,
                    "SENSOR_2": sensor.sensor_2,
                    "SENSOR_3": sensor.sensor_3,
                    "SENSOR_4": sensor.sensor_4,
                }
                self.socketio.emit("sensor_update", self.latest_data)
                self.logger.log_bin_status(self.latest_data)
                if time.time() - self.last_notification_time >= 10:
                    self.last_notification_time = time.time()
                    self.check_and_notify("bio", sensor.sensor_1, 13)
                    self.check_and_notify("non", sensor.sensor_2, 13)
                    self.check_and_notify("rec", sensor.sensor_3, 13)
                    self.check_and_notify("haz", sensor.sensor_4, 13)
        except serial.SerialException:
            print("Serial connection issue.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.socketio.emit("sensor_update", self.latest_data)
        time.sleep(2)

    def check_and_notify(self, bin_type, sensor_value, threshold):
        if sensor_value <= threshold and not self.notification_sent[bin_type]:
            self.bin_system.send_notification(bin_type)
            self.logger.log_alert({"bin_type": bin_type})
            self.alert.play_alert(bin_type)
            self.notification_sent[bin_type] = True
        elif sensor_value > threshold:
            self.notification_sent[bin_type] = False
        time.sleep(5)

    def check_thresholds(self):
        return {sensor: data > 13 for sensor, data in self.latest_data.items()}