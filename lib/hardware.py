import time
import threading
import RPi.GPIO as GPIO

class Servo:
    def __init__(self, pin1, pin2):
        self.pin1 = pin1
        self.pin2 = pin2
        self.lock = threading.Lock()
        self._setup_gpio()

    def _setup_gpio(self):
        """configure GPIO settings"""
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        for pin in (self.pin1, self.pin2):
            GPIO.setup(pin, GPIO.OUT)

    def set_angle(self, pin, angle):
        """set servo to the specified angle"""
        with self.lock:
            pwm = GPIO.PWM(pin, 50)
            pwm.start(0)
            duty = angle / 18 + 2
            GPIO.output(pin, GPIO.HIGH)
            pwm.ChangeDutyCycle(duty)
            time.sleep(1)
            GPIO.output(pin, GPIO.LOW)
            pwm.ChangeDutyCycle(0)
            pwm.stop()

    def cleanup(self):
        """release GPIO resources"""
        GPIO.cleanup()