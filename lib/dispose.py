import warnings
from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Device
import time
import threading

class Dispose:
    def __init__(self, servo_pin_1, servo_pin_2, cooldown_period=2):
        self.COOLDOWN_PERIOD = cooldown_period
        
        try:
            self.factory = PiGPIOFactory()
            print("Using PiGPIO factory for improved performance")
        except OSError:
            warnings.warn("Unable to use PiGPIO. Falling back to default factory. For better performance, run 'sudo pigpiod' before starting this script.")
            self.factory = Device.pin_factory

        self.servo1 = AngularServo(servo_pin_1, min_angle=0, max_angle=180, pin_factory=self.factory)
        self.servo2 = AngularServo(servo_pin_2, min_angle=0, max_angle=180, pin_factory=self.factory)

        self.last_action_time = time.time()
        self.servo_lock = threading.Lock()

    def set_servo_angle(self, servo, angle):
        with self.servo_lock:
            try:
                servo.angle = angle
                time.sleep(0.5)  
            except Exception as e:
                print(f"Error setting servo angle: {e}")

    def dispose(self, servo1_angle, servo2_angle):
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
        self.dispose(0, 180)

    def dispose_hazardous(self):
        print("Performing action: Disposing Dangerous/Hazardous Waste")
        self.dispose(90, 180)

    def can_perform_action(self):
        current_time = time.time()
        if current_time - self.last_action_time >= self.COOLDOWN_PERIOD:
            self.last_action_time = current_time
            return True
        else:
            print("Action prevented: Cooldown in effect")
            return False

    def cleanup(self):
        self.servo1.close()
        self.servo2.close()