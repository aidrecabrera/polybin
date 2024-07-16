from lib.data import Data


data = Data("/dev/ttyUSB0")
while True:
    data.retrieve_data()
    print(data.sensor_1)
    print(data.sensor_2)
    print(data.sensor_3)
    print(data.sensor_4)
    