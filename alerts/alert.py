import os
import sys
import threading
import time
from queue import Queue
from abc import ABC, abstractmethod
import pygame
from enum import Enum, auto

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class AlertCategory(Enum):
    REMOVE = auto()
    OTHER = auto()

class AlertStrategy(ABC):
    @abstractmethod
    def play(self, alert_system):
        pass

    @abstractmethod
    def get_category(self):
        pass

class StandardAlert(AlertStrategy):
    def __init__(self, alert_type):
        self.alert_type = alert_type

    def play(self, alert_system):
        alert_system._play_sound(alert_system.alerts[self.alert_type])
        alert_system._play_sound(alert_system.alerts["please_empty"])

    def get_category(self):
        return AlertCategory.OTHER

class RemoveAlert(AlertStrategy):
    def __init__(self, alert_type):
        self.alert_type = alert_type

    def play(self, alert_system):
        alert_system._play_sound(alert_system.alerts[self.alert_type])
        alert_system._play_sound(alert_system.alerts["remove"])

    def get_category(self):
        return AlertCategory.REMOVE

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
        self.last_play_time = {
            AlertCategory.REMOVE: 0,
            AlertCategory.OTHER: 0
        }
        self.cooldown_time = {
            AlertCategory.REMOVE: 30, 
            AlertCategory.OTHER: 300    
        }
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
            category = alert_strategy.get_category()

            if self.currently_playing.is_set():
                print(f"Alert already playing. Skipping {alert_strategy.alert_type}.")
                return

            time_since_last_play = current_time - self.last_play_time[category]
            if time_since_last_play < self.cooldown_time[category]:
                print(f"Cooldown active for {category.name}. Skipping {alert_strategy.alert_type}.")
                return

            print(f"Playing alert sound: {alert_strategy.alert_type} (Category: {category.name})")
            self.currently_playing.set()
            alert_strategy.play(self)
            self.currently_playing.clear()

            self.last_play_time[category] = current_time

    def _queue_alert(self, alert_strategy):
        if alert_strategy.alert_type in self.alerts:
            self.queue.put(alert_strategy)
        else:
            print(f"Alert type '{alert_strategy.alert_type}' not recognized.")

    def play_alert(self, alert_type):
        self._queue_alert(StandardAlert(alert_type))

    def play_remove(self, alert_type):
        self._queue_alert(RemoveAlert(alert_type))

def simulate_on_prediction(alert_system):
    alert_types = ["bio", "haz", "non", "rec"]
    for _ in range(3):
        alert_type = alert_types[_ % len(alert_types)]
        print(f"on_prediction triggered for: {alert_type}")
        alert_system.play_alert(alert_type)
        alert_system.play_remove(alert_type)
        time.sleep(0.1)

if __name__ == "__main__":
    alert_system = Alert()
    
    print("Simulating multiple on_prediction calls...")
    for _ in range(3):
        simulate_on_prediction(alert_system)
        time.sleep(1) 

    print("\nTesting individual alert types...")
    alert_types = ["bio", "haz", "non", "rec"]
    for alert_type in alert_types:
        print(f"\nTesting alert type: {alert_type}")
        alert_system.play_alert(alert_type)
        alert_system.play_remove(alert_type)
        time.sleep(1)

    print("\nTesting cooldowns...")
    print("Attempting to play 'bio' alert again immediately:")
    alert_system.play_alert("bio")
    print("Attempting to play 'remove bio' alert again immediately:")
    alert_system.play_remove("bio")

    print("\nWaiting for OTHER cooldown to expire...")
    time.sleep(31) 
    print("Attempting to play 'haz' alert after OTHER cooldown:")
    alert_system.play_alert("haz")
    print("Attempting to play 'remove haz' alert after OTHER cooldown (should still be in BIN cooldown):")
    alert_system.play_remove("haz")

    print("\nWaiting for BIN cooldown to expire...")
    time.sleep(270) 
    print("Attempting to play 'remove rec' alert after BIN cooldown:")
    alert_system.play_remove("rec")

    time.sleep(10)