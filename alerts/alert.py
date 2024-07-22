import os
import sys
import threading
import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class Alert:
    def __init__(self):
        pygame.mixer.init()
        self.alerts = {
            "bio": os.path.join(
                os.path.dirname(__file__), "biodegradable.mp3"
            ),
            "non": os.path.join(
                os.path.dirname(__file__), "non_biodegradable.mp3"
            ),
            "rec": os.path.join(os.path.dirname(__file__), "recyclable.mp3"),
            "haz": os.path.join(os.path.dirname(__file__), "hazardous.mp3"),
            "please_empty": os.path.join(os.path.dirname(__file__), "please_empty.mp3"),
            "remove": os.path.join(os.path.dirname(__file__), "remove.mp3"),
        }

    def _play_sound(self, sound_file):
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    def play_alert(self, alert_type):
        if alert_type in self.alerts:
            print("Playing alert sound: ", alert_type)
            def play_sequence():
                self._play_sound(self.alerts[alert_type])
                self._play_sound(self.alerts["please_empty"])

            threading.Thread(target=play_sequence).start()
        else:
            print(f"Alert type '{alert_type}' not recognized.")

if __name__ == "__main__":
    alert_system = Alert()
    alert_types = ["biodegradable", "hazardous", "non_biodegradable", "recyclable"]
    
    for alert_type in alert_types:
        print(f"Testing alert type: {alert_type}")
        alert_system.play_alert(alert_type)
