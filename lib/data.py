import serial
import serial.tools.list_ports
from proto import trashscan_protocol_pb2 as protocol

class Data:
    def __init__(self, serial_port):
        self.serial_port = serial_port
        self.sensor_1 = 40
        self.sensor_2 = 40
        self.sensor_3 = 40
        self.sensor_4 = 40

    def retrieve_data(self):
        """update sensor data from serial connection"""
        if not self.check_transmission():
            return False
        try:
            with serial.Serial(self.serial_port, 19200, timeout=1) as ser:
                encoded_message = ser.read(20)
                bin_status = protocol.BIN_STATUS()
                bin_status.ParseFromString(encoded_message)
                self.sensor_1 = bin_status.SENSOR_1
                self.sensor_2 = bin_status.SENSOR_2
                self.sensor_3 = bin_status.SENSOR_3
                self.sensor_4 = bin_status.SENSOR_4
            return True
        except serial.SerialException as e:
            print(f"serial error: {e}")
            return False

    def check_transmission(self):
        """check if the specified serial port is available"""
        return self.serial_port in [port.device for port in serial.tools.list_ports.comports()]