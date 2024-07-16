from lib.data import Data


data = Data("/dev/ttyUSB0")
while True:
    data.retrieve_data()
    for i in range(1, 5):
        print(f"sensor_{i}: {getattr(data, f'sensor_{i}')}")