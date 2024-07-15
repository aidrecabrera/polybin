import serial
import time

class Sms:
    def __init__(self, port, baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate

    def send_notification(self, bin_type):
        """send notification for the specified bin type"""
        commands = {'bio': 'a', 'non': 'b', 'rec': 'c', 'haz': 'd'}
        
        if bin_type not in commands:
            print(f"invalid bin type: {bin_type}")
            return False

        try:
            with serial.Serial(self.port, self.baud_rate, timeout=1) as ser:
                time.sleep(2)  # wait for connection to establish
                ser.write(commands[bin_type].encode())
                print(f"notification sent for {bin_type} bin")
            return True
        except serial.SerialException as e:
            print(f"sms error: {e}")
            return False