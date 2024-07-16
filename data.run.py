from lib.data import Data

data = Data()

data.get_bin_data('/dev/ttyACM0')
for i in range(4):
    print(f"Sensor {i+1}: {data.sensor_1}")