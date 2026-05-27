import logging
from typing import Optional

import numpy as np
import torch
from PIL import Image

logger = logging.getLogger(__name__)

_clip_model = None
_clip_preprocess = None
_clip_tokenizer = None


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
) -> Optional[dict]:
    best_match = None
    best_similarity = -1.0

    for entry in catalog:
        sim = cosine_similarity(query_embedding, entry["embedding"])
        if sim > best_similarity:
            best_similarity = sim
            best_match = entry

    if best_match and best_similarity >= threshold:
        return {"product_id": best_match["product_id"], "similarity": best_similarity}

    return None
