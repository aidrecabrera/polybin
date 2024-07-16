import serial
import serial.tools.list_ports
from proto import trashscan_protocol_pb2 as protocol
import logging

class Data:
    BAUD_RATE = 19200
    TIMEOUT = 1
    MESSAGE_SIZE = 20

    def __init__(self, serial_port=None):
        self.serial_port = serial_port
        self.sensors = {f"sensor_{i}": 40 for i in range(1, 5)}
        self.logger = logging.getLogger(__name__)

    @property
    def available_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def set_serial_port(self, port):
        if port in self.available_ports:
            self.serial_port = port
            return True
        self.logger.error(f"Serial port {port} is not available")
        return False

    def retrieve_data(self):
        """Update sensor data from serial connection"""
        if not self.serial_port:
            self.logger.error("No serial port specified")
            return False

        if self.serial_port not in self.available_ports:
            self.logger.error(f"Serial port {self.serial_port} is not available")
            return False

        try:
            with serial.Serial(self.serial_port, self.BAUD_RATE, timeout=self.TIMEOUT) as ser:
                encoded_message = ser.read(self.MESSAGE_SIZE)
                if len(encoded_message) != self.MESSAGE_SIZE:
                    self.logger.error(f"Received {len(encoded_message)} bytes, expected {self.MESSAGE_SIZE}")
                    return False

                bin_status = protocol.BIN_STATUS()
                bin_status.ParseFromString(encoded_message)
                
                for i in range(1, 5):
                    self.sensors[f"sensor_{i}"] = getattr(bin_status, f"SENSOR_{i}")
                
                return True
        except serial.SerialException as e:
            self.logger.error(f"Serial error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return False

    def get_sensor_data(self):
        """Return a dictionary of all sensor data"""
        return self.sensors.copy()

    def get_sensor_value(self, sensor_number):
        """Get the value of a specific sensor"""
        key = f"sensor_{sensor_number}"
        if key in self.sensors:
            return self.sensors[key]
        self.logger.error(f"Invalid sensor number: {sensor_number}")
        return None