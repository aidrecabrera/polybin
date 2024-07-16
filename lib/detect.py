import requests
import numpy as np
from PIL import Image
from typing import List, Dict, Tuple, Union
import io

class Detect:
    def __init__(self, api_key: str, model_id: str, confidence_threshold: float = 0.287):
        self.api_key = api_key
        self.model_id = model_id
        self.confidence_threshold = confidence_threshold
        self.api_url = f"https://detect.roboflow.com/{model_id}"
        self.class_names = ['Bio-degradable', 'Hazardous', 'Non-biodegradable', 'Recyclable']

    def perform_inference(self, image: Union[np.ndarray, str, Image.Image]) -> List[Dict[str, Union[Tuple[float, float, float, float], float, str]]]:
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        elif isinstance(image, str):
            image = Image.open(image)
        elif not isinstance(image, Image.Image):
            raise ValueError("Input must be a NumPy array, PIL Image, or a string path to an image.")

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        response = requests.post(
            self.api_url,
            data=img_byte_arr,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"API_KEY {self.api_key}"
            },
            params={
                "confidence": self.confidence_threshold,
                "overlap": 30,
                "format": "json"
            }
        )

        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

        result = response.json()

        detections = []
        for prediction in result.get('predictions', []):
            x, y, width, height = prediction['x'], prediction['y'], prediction['width'], prediction['height']
            x1, y1 = x - width / 2, y - height / 2
            x2, y2 = x + width / 2, y + height / 2
            
            detections.append({
                'bounding_box': (x1, y1, x2, y2),
                'confidence': prediction['confidence'],
                'class': prediction['class']
            })

        return detections

    def print_detections(self, detections: List[Dict[str, Union[Tuple[float, float, float, float], float, str]]]) -> None:
        for detection in detections:
            bbox = detection['bounding_box']
            conf = detection['confidence']
            cls = detection['class']
            print(f'Class: {cls}, Confidence: {conf:.2f}, Bounding Box: ({bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f})')