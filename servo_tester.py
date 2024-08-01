import warnings
from gpiozero import Servo
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

        self.servo_x = Servo(servo_pin_1, min_angle=0, max_angle=180, pin_factory=self.factory)
        self.servo_y = Servo(servo_pin_2, min_angle=0, max_angle=180, pin_factory=self.factory)

        self.last_action_time = time.time()
        self.servo_lock = threading.Lock()
        
    def reset_state(self):
        print("Resetting state")
        self.servo_x.mid()
        self.servo_y.mid()

    def dispose_non_biodegradable(self):
        # bottom-right
        print("Performing action: Disposing Non-Biodegradable")

    def dispose_biodegradable(self):
        # bottom-left
        print("Performing action: Disposing Biodegradable")

    def dispose_recyclable(self):
        # top-left
        print("Performing action: Disposing Recyclable")

    def dispose_hazardous(self):
        # top-right
        print("Performing action: Disposing Dangerous/Hazardous Waste")

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