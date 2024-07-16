import serial
import time
from config import SERIAL_PORT, SERIAL_BAUD_RATE

class Sms:
    def __init__(self, port=SERIAL_PORT, baud_rate=SERIAL_BAUD_RATE):
        self.serial_connection = serial.Serial(port, baud_rate, timeout=1)
        time.sleep(2)

    def send_notification(self, bin_type):
        commands = {
            'bio': 'a',
            'non': 'b',
            'rec': 'c',
            'haz': 'd'
        }
        if bin_type in commands:
            print(f"Sending notification for {bin_type} bin.")
            self.serial_connection.write(commands[bin_type].encode())
        else:
            print("Invalid or Error")

    def close(self):
        self.serial_connection.close()
        print("COMM Closed!")
