import serial
import serial.tools.list_ports
from proto import trashscan_protocol_pb2 as protocol

class Data:
    def __init__(self, serial_port):
        self.serial_port = serial_port
        self.sensors = {f"SENSOR_{i}": 40 for i in range(1, 5)}

    def update(self):
        """update sensor data from serial connection"""
        if not self.check_transmission():
            return False

        try:
            with serial.Serial(self.serial_port, 19200, timeout=1) as ser:
                encoded_message = ser.read(20)
                bin_status = protocol.BIN_STATUS()
                bin_status.ParseFromString(encoded_message)
                
                for i in range(1, 5):
                    self.sensors[f"SENSOR_{i}"] = getattr(bin_status, f"SENSOR_{i}")
            return True
        except serial.SerialException as e:
            print(f"serial error: {e}")
            return False

    def check_transmission(self):
        """check if the specified serial port is available"""
        return self.serial_port in [port.device for port in serial.tools.list_ports.comports()]

data = Data()

data.update()
print(data.sensors)