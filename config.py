import os
from dotenv import load_dotenv

load_dotenv()

FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
SERIAL_PORT = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")
SERIAL_BAUD_RATE = int(os.getenv("SERIAL_BAUD_RATE", 9600))
SENSOR_SERIAL_PORT = os.getenv("SENSOR_SERIAL_PORT", "/dev/ttyACM0")
NOTIFICATION_INTERVAL = int(os.getenv("NOTIFICATION_INTERVAL", 10))
SENSOR_UPDATE_INTERVAL = int(os.getenv("SENSOR_UPDATE_INTERVAL", 2))
SENSOR_THRESHOLD = int(os.getenv("SENSOR_THRESHOLD", 13))
