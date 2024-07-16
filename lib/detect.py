import torch
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
from typing import List, Dict, Tuple, Union

class Detect:
    def __init__(self, model_path: str = 'model/weights/best.pt', confidence_threshold: float = 0.287, img_size: int = 320):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.img_size = img_size
        self.model = None
        self.class_names = ['Bio-degradable', 'Hazardous', 'Non-biodegradable', 'Recyclable']
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.transform = transforms.Compose([
            transforms.Resize((self.img_size, self.img_size)),
            transforms.ToTensor(),
        ])

    def load_model(self) -> None:
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_path, force_reload=True)
        self.model.to(self.device)
        self.model.eval()

    def preprocess_image(self, image: Union[np.ndarray, str, Image.Image]) -> torch.Tensor:
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        elif isinstance(image, str):
            image = Image.open(image).convert('RGB')
        elif not isinstance(image, Image.Image):
            raise ValueError("Input must be a NumPy array, PIL Image, or a string path to an image.")

        return self.transform(image).unsqueeze(0).to(self.device)

    def perform_inference(self, image: Union[np.ndarray, str, Image.Image]) -> List[Dict[str, Union[Tuple[float, float, float, float], float, str]]]:
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() before performing inference.")
        
        img = self.preprocess_image(image)
        
        with torch.no_grad():
            results = self.model(img)

        detections = []
        for pred in results.xyxy[0]:
            if pred[4] >= self.confidence_threshold:
                x1, y1, x2, y2, conf, cls = pred.tolist()
                detections.append({
                    'bounding_box': (x1, y1, x2, y2),
                    'confidence': conf,
                    'class': self.class_names[int(cls)]
                })
        
        return detections

    def print_detections(self, detections: List[Dict[str, Union[Tuple[float, float, float, float], float, str]]]) -> None:
        for detection in detections:
            bbox = detection['bounding_box']
            conf = detection['confidence']
            cls = detection['class']
            print(f'Class: {cls}, Confidence: {conf:.2f}, Bounding Box: ({bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f})')