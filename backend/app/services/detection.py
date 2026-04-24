import io
import logging
import os
from pathlib import Path
from typing import Optional

from PIL import Image
from ultralytics import YOLO

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = Path("/app/models/best.pt")

def get_model_path() -> Path:
    env_path = os.environ.get("MODEL_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_MODEL_PATH

model: Optional[YOLO] = None


def get_model() -> YOLO:
    global model
    if model is None:
        model_path = get_model_path()
        if model_path.exists():
            logger.info(f"Loading YOLO model from {model_path}")
            model = YOLO(str(model_path))
        else:
            logger.warning(f"Model not found at {model_path}, falling back to YOLOv8n")
            model = YOLO("yolov8n.pt")
    return model


def get_model_classes() -> dict:
    model = get_model()
    return model.names if model else {}


def detect_in_image(image: Image.Image, conf_threshold: float = 0.05) -> dict:
    if image.mode != "RGB":
        image = image.convert("RGB")

    yolo_model = get_model()
    results = yolo_model.predict(image, conf=conf_threshold, verbose=False)

    detections = []
    for r in results:
        for box in r.boxes:
            detections.append({
                "class": yolo_model.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy[0].tolist()
            })

    return {
        "detections": detections,
        "image_size": [image.width, image.height]
    }
