import RPi.GPIO as GPIO
import time
import threading

class Dispose:
    def __init__(self, servo_pin_1, servo_pin_2, cooldown_period=2):
        self.SERVO_PIN_1 = servo_pin_1
        self.SERVO_PIN_2 = servo_pin_2
        self.COOLDOWN_PERIOD = cooldown_period

        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.SERVO_PIN_1, GPIO.OUT)
        GPIO.setup(self.SERVO_PIN_2, GPIO.OUT)

        self.last_action_time = time.time()
        self.servo_lock = threading.Lock()

    def set_servo_angle(self, servo_pin, angle):
        with self.servo_lock:
            pwm = GPIO.PWM(servo_pin, 50)
            pwm.start(0)
            duty = angle / 18 + 2
            GPIO.output(servo_pin, GPIO.HIGH)
            
            current_duty = 0
            step = 0.5 
            while current_duty < duty:
                current_duty += step
                pwm.ChangeDutyCycle(current_duty)
                time.sleep(0.1) 
            
            time.sleep(1)
            GPIO.output(servo_pin, GPIO.LOW)
            pwm.ChangeDutyCycle(0)
            pwm.stop()

    def dispose(self, servo1_angle, servo2_angle):
        self.set_servo_angle(self.SERVO_PIN_1, servo1_angle)
        self.set_servo_angle(self.SERVO_PIN_2, servo2_angle)
        time.sleep(1.5)
        self.set_servo_angle(self.SERVO_PIN_2, 90)

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
        GPIO.cleanup()
