import pytest
from unittest.mock import patch, MagicMock
from lib.data import Data
from proto import trashscan_protocol_pb2

@pytest.fixture
def data():
    return Data()

def test_init(data):
    assert data.sensor_1 == 40
    assert data.sensor_2 == 40
    assert data.sensor_3 == 40
    assert data.sensor_4 == 40

@patch('serial.Serial')
def test_get_bin_data(mock_serial, data):
    mock_serial.return_value.read.return_value = b'some_encoded_message'
    with patch.object(trashscan_protocol_pb2.BIN_STATUS, 'ParseFromString', return_value=None) as mock_parse:
        bin_status = trashscan_protocol_pb2.BIN_STATUS()
        bin_status.SENSOR_1 = 40
        bin_status.SENSOR_2 = 40
        bin_status.SENSOR_3 = 40
        bin_status.SENSOR_4 = 40
        mock_parse.side_effect = lambda x: setattr(data, 'sensor_1', bin_status.SENSOR_1) or setattr(data, 'sensor_2', bin_status.SENSOR_2) or setattr(data, 'sensor_3', bin_status.SENSOR_3) or setattr(data, 'sensor_4', bin_status.SENSOR_4)
        data.get_bin_data('/dev/ttyACM0')
        assert data.sensor_1 != 40
        assert data.sensor_2 != 40
        assert data.sensor_3 != 40
        assert data.sensor_4 != 40

@patch('serial.tools.list_ports.comports')
def test_check_transmission(mock_comports, data):
    mock_comports.return_value = [MagicMock(device='/dev/ttyACM0'), MagicMock(device='/dev/ttyACM1')]
    assert data.check_transmission('/dev/ttyACM0') is True
    assert data.check_transmission('/dev/ttyUSB0') is False