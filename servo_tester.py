from gpiozero import AngularServo
import time
import threading

class Dispose:
    def __init__(self, servo_pin_1, servo_pin_2, cooldown_period=2):
        self.COOLDOWN_PERIOD = cooldown_period

        self.servo1 = AngularServo(servo_pin_1, min_angle=0, max_angle=180)
        self.servo2 = AngularServo(servo_pin_2, min_angle=0, max_angle=180)

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

def main():
    servo_pin_1 = 12  
    servo_pin_2 = 19  
    cooldown_period = 2

    dispose_system = Dispose(servo_pin_1, servo_pin_2, cooldown_period)

    try:
        while True:
            action = input("Enter action (1: biodegradable, 2: non_biodegradable, 3: recyclable, 4: hazardous) or 'exit' to quit: ").strip().lower()
            
            if action == 'exit':
                break

            if dispose_system.can_perform_action():
                if action == "1":
                    dispose_system.dispose_biodegradable()
                elif action == "2":
                    dispose_system.dispose_non_biodegradable()
                elif action == "3":
                    dispose_system.dispose_recyclable()
                elif action == "4":
                    dispose_system.dispose_hazardous()
                else:
                    print("Invalid action. Please enter a valid action.")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Cleaning up...")
    finally:
        dispose_system.cleanup()

if __name__ == "__main__":
    main()