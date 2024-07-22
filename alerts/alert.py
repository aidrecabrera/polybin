import os
import sys
import threading
import time
from queue import Queue
from abc import ABC, abstractmethod
import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class AlertStrategy(ABC):
    @abstractmethod
    def play(self, alert_system):
        pass

class StandardAlert(AlertStrategy):
    def __init__(self, alert_type):
        self.alert_type = alert_type

    def play(self, alert_system):
        alert_system._play_sound(alert_system.alerts[self.alert_type])
        alert_system._play_sound(alert_system.alerts["please_empty"])

class RemoveAlert(AlertStrategy):
    def __init__(self, alert_type):
        self.alert_type = alert_type

    def play(self, alert_system):
        alert_system._play_sound(alert_system.alerts[self.alert_type])
        alert_system._play_sound(alert_system.alerts["remove"])

class Alert:
    def __init__(self):
        pygame.mixer.init()
        self.alerts = {
            "bio": os.path.join(os.path.dirname(__file__), "biodegradable.mp3"),
            "non": os.path.join(os.path.dirname(__file__), "non_biodegradable.mp3"),
            "rec": os.path.join(os.path.dirname(__file__), "recyclable.mp3"),
            "haz": os.path.join(os.path.dirname(__file__), "hazardous.mp3"),
            "please_empty": os.path.join(os.path.dirname(__file__), "please_empty.mp3"),
            "remove": os.path.join(os.path.dirname(__file__), "remove.mp3"),
        }
        self.last_play_times = {}
        self.last_alert_type = None
        self.cooldown_time = 5
        self.repetition_prevention_time = 2
        self.lock = threading.Lock()
        self.queue = Queue()
        self.currently_playing = threading.Event()
        threading.Thread(target=self._process_queue, daemon=True).start()

    def _play_sound(self, sound_file):
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    def _process_queue(self):
        while True:
            alert_strategy = self.queue.get()
            self._play_alert(alert_strategy)
            self.queue.task_done()

    def _play_alert(self, alert_strategy):
        with self.lock:
            current_time = time.time()
            alert_type = alert_strategy.alert_type

            if self.currently_playing.is_set():
                print(f"Alert already playing. Skipping {alert_type}.")
                return

            if alert_type in self.last_play_times:
                time_since_last_play = current_time - self.last_play_times[alert_type]
                if time_since_last_play < self.cooldown_time:
                    print(f"Cooldown active for {alert_type}. Skipping.")
                    return

            if self.last_alert_type == alert_type and (current_time - self.last_play_times.get(alert_type, 0)) < self.repetition_prevention_time:
                print(f"Preventing rapid repetition of {alert_type}. Skipping.")
                return

            print(f"Playing alert sound: {alert_type}")
            self.currently_playing.set()
            alert_strategy.play(self)
            self.currently_playing.clear()

            self.last_play_times[alert_type] = current_time
            self.last_alert_type = alert_type

    def play_alert(self, alert_type):
        if alert_type in self.alerts:
            self.queue.put(StandardAlert(alert_type))
        else:
            print(f"Alert type '{alert_type}' not recognized.")

    def play_remove(self, alert_type):
        if alert_type in self.alerts:
            self.queue.put(RemoveAlert(alert_type))
        else:
            print(f"Alert type '{alert_type}' not recognized.")