import serial
import time

class Sms:
    def __init__(self, port="/dev/ttyUSB0", baud_rate=9600):
        # initializing serial connection
        self.serial_connection = serial.Serial(port, baud_rate, timeout=1)
        # wait for 2 seconds to establish connection
        time.sleep(2)

    def send_notification(self, bin_type):
        # define command mapping for different bin types
        commands = {
            'bio': 'a',
            'non': 'b',
            'rec': 'c',
            'haz': 'd'
        }
        # check if the bin_type is valid
        if bin_type in commands:
            # sending the appropriate command for the bin type
            print(f"sending notification for {bin_type} bin.")
            self.serial_connection.write(commands[bin_type].encode())
        else:
            # handle invalid bin type
            print("invalid or error")

    def close(self):
        # closing the serial connection
        self.serial_connection.close()
        print("comm closed!")
