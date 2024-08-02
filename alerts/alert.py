import os
import threading
import time
from queue import Queue
import pygame

class Alert:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Alert, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.alerts = {
            "bio": os.path.join(os.path.dirname(__file__), "biodegradable.mp3"),
            "non": os.path.join(os.path.dirname(__file__), "non_biodegradable.mp3"),
            "rec": os.path.join(os.path.dirname(__file__), "recyclable.mp3"),
            "haz": os.path.join(os.path.dirname(__file__), "hazardous.mp3"),
            "please_empty": os.path.join(os.path.dirname(__file__), "please_empty.mp3"),
            "remove": os.path.join(os.path.dirname(__file__), "remove.mp3"),
        }
        self.queue = Queue()
        self._initialize_pygame_mixer()
        threading.Thread(target=self._process_queue, daemon=True).start()

    def _initialize_pygame_mixer(self, retries=5, delay=2):
        for attempt in range(retries):
            try:
                pygame.mixer.init()
                print("Pygame mixer initialized successfully.")
                return
            except pygame.error as e:
                print(f"Attempt {attempt + 1} to initialize pygame.mixer failed: {e}")
                if attempt < retries - 1:
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print("Failed to initialize pygame.mixer after several attempts.")
                    print("Sounds will not be played. Please check your audio setup.")

    def _process_queue(self):
        while True:
            alert_type = self.queue.get()
            self._play_sound(self.alerts[alert_type])
            self.queue.task_done()

    def _play_sound(self, sound_file):
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            except pygame.error as e:
                print(f"Failed to play sound {sound_file}: {e}")
        else:
            print(f"Cannot play sound {sound_file}: Pygame mixer is not initialized.")

    def play_alert(self, alert_type):
        if alert_type in self.alerts:
            self.queue.put(alert_type)
        else:
            print(f"Alert type '{alert_type}' not recognized.")

    def play_remove(self, alert_type):
        if alert_type in self.alerts:
            self.queue.put(alert_type)
            self.queue.put("remove")
        else:
            print(f"Alert type '{alert_type}' not recognized.")