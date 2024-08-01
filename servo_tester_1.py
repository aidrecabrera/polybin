from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Device
import time
import warnings

class Dispose:
    def __init__(self, servo_pin_1, servo_pin_2):
        try:
            self.factory = PiGPIOFactory()
            print("Using PiGPIO factory for improved performance")
        except OSError:
            warnings.warn("Unable to use PiGPIO. Falling back to default factory. For better performance, run 'sudo pigpiod' before starting this script.")
            self.factory = Device.pin_factory

        self.servo1 = AngularServo(servo_pin_1, min_angle=0, max_angle=180, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=self.factory)
        self.servo2 = AngularServo(servo_pin_2, min_angle=0, max_angle=180, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=self.factory)

    def set_servo_angle(self, servo, angle):
        try:
            servo.angle = angle
            print(f"Setting servo on pin {servo.pin} to angle {angle}")
            time.sleep(0.5)  
        except Exception as e:
            print(f"Error setting servo angle: {e}")

    def test_servo(self, servo, name):
        print(f"Testing {name}")
        for angle in [0, 90, 180, 90, 0]:
            self.set_servo_angle(servo, angle)
            time.sleep(1)

    def cleanup(self):
        self.servo1.close()
        self.servo2.close()

def main():
    servo_pin_1 = 12
    servo_pin_2 = 19

    try:
        dispose_system = Dispose(servo_pin_1, servo_pin_2)
    except Exception as e:
        print(f"Error initializing Dispose system: {e}")
        print("Please check your GPIO connections and permissions.")
        return

    try:
        while True:
            action = input("Enter action (1: test servo 1, 2: test servo 2, 3: test both) or 'exit' to quit: ").strip().lower()
            
            if action == 'exit':
                break

            if action == "1":
                dispose_system.test_servo(dispose_system.servo1, "Servo 1")
            elif action == "2":
                dispose_system.test_servo(dispose_system.servo2, "Servo 2")
            elif action == "3":
                dispose_system.test_servo(dispose_system.servo1, "Servo 1")
                dispose_system.test_servo(dispose_system.servo2, "Servo 2")
            else:
                print("Invalid action. Please enter a valid action.")
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Cleaning up...")
    finally:
        dispose_system.cleanup()

if __name__ == "__main__":
    main()