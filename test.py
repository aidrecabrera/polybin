import time
from lib.dispose import Dispose

def main():
    servo_controller = Dispose(servo_pin_1=32, servo_pin_2=35)
    try:
        while True:
            print("\nSelect the type of waste to dispose:")
            print("1: Biodegradable")
            print("2: Non-Biodegradable")
            print("3: Recyclable")
            print("4: Dangerous/Hazardous")
            print("q: Quit")

            user_input = input("Enter your choice: ")

            if user_input == '1':
                if servo_controller.can_perform_action():
                    servo_controller.dispose_biodegradable()
            elif user_input == '2':
                if servo_controller.can_perform_action():
                    servo_controller.dispose_non_biodegradable()
            elif user_input == '3':
                if servo_controller.can_perform_action():
                    servo_controller.dispose_recyclable()
            elif user_input == '4':
                if servo_controller.can_perform_action():
                    servo_controller.dispose_dangerous()
            elif user_input.lower() == 'q':
                break
            else:
                print("Invalid choice. Please try again.")
            
            time.sleep(1) 

    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        servo_controller.cleanup()

if __name__ == "__main__":
    main()
