# Initialize the Data object
from lib.data import Data

data = Data()
if data.set_serial_port("/dev/ttyACM0"): 
    if data.retrieve_data():
        all_sensors = data.get_sensor_data()
        print(all_sensors)
        sensor_2_value = data.get_sensor_value(2)
        print(f"Sensor 2 value: {sensor_2_value}")
    else:
        print("Failed to retrieve data")
else:
    print("Failed to set serial port")