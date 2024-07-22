import os
import sys
import threading
from playsound import playsound

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class Alert:
    def __init__(self):
        self.alerts = {
            "biodegradable": os.path.join(
                os.path.dirname(__file__), "biodegradable.mp3"
            ),
            "hazardous": os.path.join(os.path.dirname(__file__), "hazardous.mp3"),
            "non_biodegradable": os.path.join(
                os.path.dirname(__file__), "non_biodegradable.mp3"
            ),
            "recyclable": os.path.join(os.path.dirname(__file__), "recyclable.mp3"),
            "please_empty": os.path.join(os.path.dirname(__file__), "please_empty.mp3"),
        }

    def _play_sound(self, sound_file):
        playsound(sound_file)

    def play_alert(self, alert_type):
        if alert_type in self.alerts:
            print("Playing alert sound: ", alert_type)
            # def play_sequence():
            #     self._play_sound(self.alerts[alert_type])
            #     self._play_sound(self.alerts["please_empty"])

            # threading.Thread(target=play_sequence).start()
        else:
            print(f"Alert type '{alert_type}' not recognized.")
