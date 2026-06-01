import io
import json
import logging
import os
from pathlib import Path
from typing import Optional

from PIL import Image
from ultralytics import YOLO

from backend.app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = Path("/app/models/best.pt")
LOCAL_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "best.pt"

DEFAULT_CLASS_THRESHOLDS = {
    "accessories": 0.30,
    "bags": 0.35,
    "clothing": 0.50,
    "shoes": 0.45,
}


def _parse_json_setting(raw: str, default: dict) -> dict:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning(f"Invalid JSON setting '{raw}': {e}. Using defaults.")
    return default


def _parse_class_thresholds() -> dict[str, float]:
    raw = _parse_json_setting(settings.YOLO_CLASS_THRESHOLDS, DEFAULT_CLASS_THRESHOLDS)
    return {k: float(v) for k, v in raw.items()}


def _parse_bbox_constraints() -> tuple[dict[str, float], dict[str, float]]:
    area_raw = _parse_json_setting(settings.BBOX_MAX_AREA_RATIO, {})
    y_raw = _parse_json_setting(settings.BBOX_MAX_Y_RATIO, {})
    area = {k: float(v) for k, v in area_raw.items()}
    y_ratio = {k: float(v) for k, v in y_raw.items()}
    return area, y_ratio


def clamp_bbox(
    bbox: list[float],
    class_name: str,
    img_width: int,
    img_height: int,
    area_constraints: dict[str, float],
    y_constraints: dict[str, float],
) -> list[float]:
    x1, y1, x2, y2 = bbox
    orig_x1, orig_y1, orig_x2, orig_y2 = x1, y1, x2, y2

    max_area_ratio = area_constraints.get(class_name)
    if max_area_ratio is not None:
        bbox_w = x2 - x1
        bbox_h = y2 - y1
        bbox_area = bbox_w * bbox_h
        img_area = img_width * img_height
        if bbox_area > max_area_ratio * img_area:
            scale = ((max_area_ratio * img_area) / bbox_area) ** 0.5
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            new_w, new_h = bbox_w * scale, bbox_h * scale
            x1, y1 = cx - new_w / 2, cy - new_h / 2
            x2, y2 = cx + new_w / 2, cy + new_h / 2
            logger.debug(
                f"Clamped bbox area for {class_name}: "
                f"{bbox_area/img_area:.1%} -> {max_area_ratio:.0%}"
            )

    max_y_ratio = y_constraints.get(class_name)
    if max_y_ratio is not None:
        max_y = img_height * max_y_ratio
        if class_name == "shoes":
            min_y = img_height * (1.0 - max_y_ratio)
            if y1 < min_y:
                y1 = min_y
                logger.debug(f"Clamped bbox y_min for shoes to {min_y}")
        else:
            if y2 > max_y:
                y2 = max_y
                logger.debug(f"Clamped bbox y_max for {class_name} to {max_y}")

    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(img_width, x2)
    y2 = min(img_height, y2)

    if x2 <= x1 or y2 <= y1:
        logger.warning(
            f"bbox clamp produced invalid bbox [{x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f}] "
            f"for {class_name}, reverting to original"
        )
        return [max(0, orig_x1), max(0, orig_y1),
                min(img_width, orig_x2), min(img_height, orig_y2)]

    return [x1, y1, x2, y2]


def get_model_path() -> Path:
    env_path = os.environ.get("MODEL_PATH")
    if env_path:
        return Path(env_path)
    if DEFAULT_MODEL_PATH.exists():
        return DEFAULT_MODEL_PATH
    if LOCAL_MODEL_PATH.exists():
        return LOCAL_MODEL_PATH
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


def _normalize_bbox(bbox: list[float]) -> list[float]:
    x1, y1, x2, y2 = bbox
    return [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]


def _compute_iou(box_a: list[float], box_b: list[float]) -> float:
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union_area = area_a + area_b - inter_area
    return inter_area / union_area if union_area > 0 else 0.0


def _dedup_by_iou(detections: list[dict], iou_threshold: float = 0.5) -> list[dict]:
    if len(detections) <= 1:
        return detections
    deduped = []
    for det in sorted(detections, key=lambda d: d["confidence"], reverse=True):
        if not any(
            det["class"] == kept["class"]
            and _compute_iou(det["bbox"], kept["bbox"]) > iou_threshold
            for kept in deduped
        ):
            deduped.append(det)
    return deduped


def detect_in_image(
    image: Image.Image,
    conf_threshold: float = 0.50,
    class_thresholds: Optional[dict[str, float]] = None,
    enable_tta: Optional[bool] = None,
) -> dict:
    if image.mode != "RGB":
        image = image.convert("RGB")

    if class_thresholds is None:
        class_thresholds = _parse_class_thresholds()

    if enable_tta is None:
        enable_tta = settings.YOLO_TTA_ENABLED

    min_conf = min(class_thresholds.values()) if class_thresholds else conf_threshold

    area_constraints, y_constraints = _parse_bbox_constraints()
    img_w, img_h = image.width, image.height

    yolo_model = get_model()

    if enable_tta:
        logger.debug("Running YOLO with TTA (augment=True)")
        results = yolo_model.predict(image, conf=min_conf, augment=True, verbose=False)
    else:
        results = yolo_model.predict(image, conf=min_conf, verbose=False)

    detections = []
    for r in results:
        for box in r.boxes:
            class_name = yolo_model.names[int(box.cls)]
            cls_threshold = class_thresholds.get(class_name, min_conf)
            raw_conf = float(box.conf)
            if raw_conf < cls_threshold:
                continue
            raw_bbox = _normalize_bbox(box.xyxy[0].tolist())
            clamped_bbox = clamp_bbox(
                raw_bbox, class_name, img_w, img_h,
                area_constraints, y_constraints,
            )
            detections.append({
                "class": class_name,
                "confidence": raw_conf,
                "bbox": clamped_bbox,
            })

    detections = _dedup_by_iou(detections)

    return {
        "detections": detections,
        "image_size": [image.width, image.height],
    }
