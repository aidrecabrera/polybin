import os
import sys
import serial
import serial.tools.list_ports
from lib import trashscan_protocol_pb2 as protocol

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class Data:
    def __init__(self):
        # initializing sensor values
        self.sensor_1 = 40
        self.sensor_2 = 40
        self.sensor_3 = 40
        self.sensor_4 = 40
        
    def get_bin_data(self):
        # establishing serial connection
        ser = serial.Serial('/dev/ttyACM0', 19200)
        # reading encoded message from serial
        encoded_message = ser.read(20)
        # parsing encoded message using protocol buffer
        bin_status = protocol.BIN_STATUS()
        bin_status.ParseFromString(encoded_message)
        # updating sensor values
        self.sensor_1 = bin_status.SENSOR_1
        self.sensor_2 = bin_status.SENSOR_2
        self.sensor_3 = bin_status.SENSOR_3
        self.sensor_4 = bin_status.SENSOR_4

    def check_transmission(self, serial_port='/dev/ttyACM0'):
        # retrieving list of available ports
        ports = [port.device for port in serial.tools.list_ports.comports()]
        # checking if the specified serial port is available
        return serial_port in ports
