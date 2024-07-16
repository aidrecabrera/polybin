import unittest
from unittest.mock import patch, MagicMock
from lib.sms import Sms

class TestSms(unittest.TestCase):
    @patch('sms.serial.Serial')
    def test_init_default(self, mock_serial):
        sms = Sms()
        mock_serial.assert_called_with('/dev/ttyUSB0', 9600, timeout=1)

    @patch('sms.serial.Serial')
    def test_init_custom(self, mock_serial):
        sms = Sms(port='/dev/ttyUSB0', baud_rate=115200)
        mock_serial.assert_called_with('/dev/ttyUSB0', 115200, timeout=1)

    @patch('sms.serial.Serial')
    def test_send_notification_valid(self, mock_serial):
        sms = Sms()
        sms.serial_connection.write = MagicMock()
        sms.send_notification('bio')
        sms.serial_connection.write.assert_called_with(b'a')

    @patch('sms.serial.Serial')
    def test_send_notification_invalid(self, mock_serial):
        sms = Sms()
        with self.assertLogs(level='INFO') as log:
            sms.send_notification('unknown')
            self.assertIn('Invalid or Error', log.output[0])

    @patch('sms.serial.Serial')
    def test_close(self, mock_serial):
        sms = Sms()
        sms.close()
        mock_serial.return_value.close.assert_called()

if __name__ == '__main__':
    unittest.main()