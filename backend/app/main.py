import os
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import io
import logging

from ultralytics import YOLO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FashionVision AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = Path(__file__).parent.parent / "models" / "best.pt"
model = None


def get_model():
    global model
    if model is None:
        if MODEL_PATH.exists():
            logger.info(f"Loading model from {MODEL_PATH}")
            model = YOLO(str(MODEL_PATH))
        else:
            logger.warning(f"Model not found at {MODEL_PATH}, using YOLOv8n")
            model = YOLO("yolov8n.pt")
    return model


@app.get("/")
async def root():
    return {"message": "FashionVision AI API", "status": "operational"}


@app.get("/health")
async def health_check():
    yolo_model = get_model()
    return {"status": "healthy", "model_loaded": yolo_model is not None}


@app.post("/api/detect")
async def detect_clothes(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        if image.mode != "RGB":
            image = image.convert("RGB")

        yolo_model = get_model()
        results = yolo_model.predict(image, conf=0.05, verbose=False)

        detections = []
        for r in results:
            for box in r.boxes:
                detections.append({
                    "class": yolo_model.names[int(box.cls)],
                    "confidence": float(box.conf),
                    "bbox": box.xyxy[0].tolist()
                })

        return JSONResponse({
            "detections": detections,
            "image_size": [image.width, image.height]
        })

    except Exception as e:
        logger.error(f"Error during detection: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
