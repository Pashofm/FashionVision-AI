import logging
from typing import Optional

import numpy as np
import torch
from PIL import Image

logger = logging.getLogger(__name__)

_clip_model = None
_clip_preprocess = None
_clip_tokenizer = None

_CLASS_PROMPTS = {
    "accessories": [
        "a photo of an accessory",
        "a photo of a hat or cap or scarf or belt",
    ],
    "bags": [
        "a photo of a bag",
        "a photo of a handbag or backpack",
    ],
    "clothing": [
        "a photo of clothing",
        "a photo of a shirt or pants or dress",
    ],
    "shoes": [
        "a photo of shoes",
        "a photo of footwear or sneakers",
    ],
}

_text_embeddings_cache = None
_text_tokenizer = None


def _get_text_tokenizer():
    global _text_tokenizer
    if _text_tokenizer is None:
        import open_clip
        _text_tokenizer = open_clip.get_tokenizer("ViT-B-32")
        logger.info("CLIP text tokenizer loaded")
    return _text_tokenizer


def get_clip_model():
    global _clip_model, _clip_preprocess, _clip_tokenizer
    if _clip_model is None:
        import open_clip

        logger.info("Loading CLIP model ViT-B-32 (laion2b_s34b_b79k)...")
        _clip_model, _clip_preprocess, _clip_tokenizer = (
            open_clip.create_model_and_transforms(
                "ViT-B-32", pretrained="laion2b_s34b_b79k"
            )
        )
        _clip_model.eval()
        logger.info("CLIP model loaded successfully")
    return _clip_model, _clip_preprocess, _clip_tokenizer


def generate_image_embedding(image: Image.Image) -> list[float]:
    model, preprocess, _ = get_clip_model()

    if image.mode != "RGB":
        image = image.convert("RGB")

    img_tensor = preprocess(image).unsqueeze(0)

    with torch.no_grad():
        image_features = model.encode_image(img_tensor)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)

    embedding = image_features.squeeze(0).tolist()
    return embedding


def _get_class_text_embeddings() -> dict[str, np.ndarray]:
    global _text_embeddings_cache

    if _text_embeddings_cache is not None:
        return _text_embeddings_cache

    model = get_clip_model()[0]
    tokenizer = _get_text_tokenizer()

    class_vectors = {}
    with torch.no_grad():
        for class_name, prompts in _CLASS_PROMPTS.items():
            text_tokens = tokenizer(prompts)
            text_features = model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            avg_vector = text_features.mean(dim=0)
            avg_vector = avg_vector / avg_vector.norm(dim=-1, keepdim=True)
            class_vectors[class_name] = avg_vector.cpu().numpy()

    _text_embeddings_cache = class_vectors
    logger.info("CLIP class text embeddings cached")
    return _text_embeddings_cache


def verify_class_clip(image: Image.Image) -> tuple[str, float]:
    model, preprocess, _ = get_clip_model()

    if image.mode != "RGB":
        image = image.convert("RGB")

    img_tensor = preprocess(image).unsqueeze(0)

    with torch.no_grad():
        image_features = model.encode_image(img_tensor)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)

    img_vector = image_features.squeeze(0).cpu().numpy()
    return verify_class_from_embedding(img_vector)


def verify_class_from_embedding(img_vector: np.ndarray) -> tuple[str, float]:
    class_embeddings = _get_class_text_embeddings()

    best_class = None
    best_sim = -1.0
    for class_name, class_vector in class_embeddings.items():
        sim = float(np.dot(img_vector, class_vector))
        if sim > best_sim:
            best_sim = sim
            best_class = class_name

    return best_class, best_sim


def refine_bbox_for_class(
    image: Image.Image,
    bbox: list[float],
    target_class: str,
    img_width: int,
    img_height: int,
) -> list[float]:
    x1, y1, x2, y2 = bbox

    if x1 >= x2 or y1 >= y2:
        logger.warning(f"Invalid bbox for refine: {bbox}, skipping refinement")
        return bbox

    bbox_h = y2 - y1
    if bbox_h < 60:
        return bbox

    crops = [
        ("top_half", x1, y1, x2, y1 + bbox_h * 0.5),
        ("top_third", x1, y1, x2, y1 + bbox_h * 0.33),
        ("top_quarter", x1, y1, x2, y1 + bbox_h * 0.25),
    ]

    best_bbox = bbox
    best_conf = -1.0

    from backend.app.config import settings

    for _label, cx1, cy1, cx2, cy2 in crops:
        cx1 = max(0, int(cx1))
        cy1 = max(0, int(cy1))
        cx2 = min(img_width, int(cx2))
        cy2 = min(img_height, int(cy2))
        if cx2 - cx1 < 20 or cy2 - cy1 < 20:
            continue
        try:
            cropped = image.crop((cx1, cy1, cx2, cy2))
            _, conf = verify_class_clip(cropped)
            if conf > best_conf:
                best_conf = conf
                best_bbox = [float(cx1), float(cy1), float(cx2), float(cy2)]
        except Exception:
            continue

    if best_bbox != bbox:
        logger.info(
            f"bbox refined for {target_class}: {bbox} -> {best_bbox} "
            f"(class_conf={best_conf:.3f})"
        )
    return best_bbox


def generate_product_embedding(images: list[Image.Image]) -> list[float]:
    embeddings = [generate_image_embedding(img) for img in images]

    avg_embedding = np.mean(embeddings, axis=0)
    norm = np.linalg.norm(avg_embedding)
    if norm > 0:
        avg_embedding = avg_embedding / norm

    return avg_embedding.tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return float(np.dot(a, b))


def find_best_match(
    query_embedding: list[float],
    catalog: list[dict],
    threshold: float = 0.25,
    gap_threshold: Optional[float] = None,
) -> Optional[dict]:
    if not catalog:
        return None

    if gap_threshold is None:
        from backend.app.config import settings
        gap_threshold = settings.CLIP_GAP_THRESHOLD

    best_match = None
    best_similarity = -1.0
    second_best_similarity = -1.0

    for entry in catalog:
        sim = cosine_similarity(query_embedding, entry["embedding"])
        if sim > best_similarity:
            second_best_similarity = best_similarity
            best_similarity = sim
            best_match = entry
        elif sim > second_best_similarity:
            second_best_similarity = sim

    if not best_match or best_similarity < threshold:
        return None

    if len(catalog) >= 2 and gap_threshold > 0:
        gap = best_similarity - second_best_similarity
        if gap < gap_threshold:
            logger.debug(
                f"CLIP match rejected: top-1={best_similarity:.4f} "
                f"top-2={second_best_similarity:.4f} gap={gap:.4f} < "
                f"gap_threshold={gap_threshold}"
            )
            return None
        logger.debug(
            f"CLIP match: sim={best_similarity:.4f} gap={gap:.4f} "
            f"(product={best_match['product_id']})"
        )

    return {"product_id": best_match["product_id"], "similarity": best_similarity}
