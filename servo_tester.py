from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Device
import time
import threading
import warnings

class Dispose:
    def __init__(self, servo_pin_1, servo_pin_2, cooldown_period=2):
        self.COOLDOWN_PERIOD = cooldown_period
        
        try:
            self.factory = PiGPIOFactory()
            print("Using PiGPIO factory for improved performance")
        except OSError:
            warnings.warn("Unable to use PiGPIO. Falling back to default factory. For better performance, run 'sudo pigpiod' before starting this script.")
            self.factory = Device.pin_factory

        self.servo1 = AngularServo(servo_pin_1, min_angle=0, max_angle=180, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=self.factory)
        self.servo2 = AngularServo(servo_pin_2, min_angle=0, max_angle=180, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=self.factory)

        self.last_action_time = time.time()
        self.servo_lock = threading.Lock()

    def set_servo_angle(self, servo, angle):
        with self.servo_lock:
            try:
                servo.angle = angle
                print(f"Setting servo on pin {servo.pin} to angle {angle}")
                time.sleep(0.5)  
            except Exception as e:
                print(f"Error setting servo angle: {e}")

    def dispose(self, servo1_angle, servo2_angle):
        if not self.can_perform_action():
            return

        try:
            self.set_servo_angle(self.servo1, servo1_angle)
            self.set_servo_angle(self.servo2, servo2_angle)
            time.sleep(1)
            self.set_servo_angle(self.servo2, 90) 
        except Exception as e:
            print(f"Error during dispose action: {e}")

    def dispose_biodegradable(self):
        print("Performing action: Disposing Biodegradable")
        self.dispose(0, 0)

    def dispose_non_biodegradable(self):
        print("Performing action: Disposing Non-Biodegradable")
        self.dispose(90, 0)

    def dispose_recyclable(self):
        print("Performing action: Disposing Recyclable")
        self.dispose(180, 0)

    def dispose_hazardous(self):
        print("Performing action: Disposing Dangerous/Hazardous Waste")
        self.dispose(180, 180)

    def can_perform_action(self):
        current_time = time.time()
        if current_time - self.last_action_time >= self.COOLDOWN_PERIOD:
            self.last_action_time = current_time
            return True
        else:
            print("Action prevented: Cooldown in effect")
            return False

    def test_servos(self):
        print("Testing Servo 1")
        self.set_servo_angle(self.servo1, 0)
        time.sleep(1)
        self.set_servo_angle(self.servo1, 90)
        time.sleep(1)
        self.set_servo_angle(self.servo1, 180)
        time.sleep(1)
        self.set_servo_angle(self.servo1, 90)
        
        print("Testing Servo 2")
        self.set_servo_angle(self.servo2, 0)
        time.sleep(1)
        self.set_servo_angle(self.servo2, 90)
        time.sleep(1)
        self.set_servo_angle(self.servo2, 180)
        time.sleep(1)
        self.set_servo_angle(self.servo2, 90)

    def cleanup(self):
        self.servo1.close()
        self.servo2.close()

def main():
    servo_pin_1 = 12
    servo_pin_2 = 19  
    cooldown_period = 2

    try:
        dispose_system = Dispose(servo_pin_1, servo_pin_2, cooldown_period)
    except Exception as e:
        print(f"Error initializing Dispose system: {e}")
        print("Please check your GPIO connections and permissions.")
        return

    try:
        print("Testing servos...")
        dispose_system.test_servos()
        print("Servo test complete. Did both servos move?")

        while True:
            action = input("Enter action (1: biodegradable, 2: non_biodegradable, 3: recyclable, 4: hazardous, 5: test servos) or 'exit' to quit: ").strip().lower()
            
            if action == 'exit':
                break

            if action == "1":
                dispose_system.dispose_biodegradable()
            elif action == "2":
                dispose_system.dispose_non_biodegradable()
            elif action == "3":
                dispose_system.dispose_recyclable()
            elif action == "4":
                dispose_system.dispose_hazardous()
            elif action == "5":
                dispose_system.test_servos()
            else:
                print("Invalid action. Please enter a valid action.")
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Cleaning up...")
    finally:
        dispose_system.cleanup()

if __name__ == "__main__":
    main()