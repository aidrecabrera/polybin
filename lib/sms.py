import serial
import time

class BinNotificationSystem:
    def __init__(self, port="/dev/ttyUSB0", baud_rate=9600):
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
        
if __name__ == "__main__":
    port = 'COM6'
    bin_system = BinNotificationSystem(port)
    try:
        bin_system.send_notification('bio')
        time.sleep(5)
        bin_system.send_notification('non')
        time.sleep(5)
        bin_system.send_notification('rec')
        time.sleep(5)
        bin_system.send_notification('haz')
        time.sleep(5)
    finally:
        bin_system.close()