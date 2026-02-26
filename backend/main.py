from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FashionVision AI API")

# IMPORTANTE: Esto permite que React (puerto 5173) hable con FastAPI (puerto 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se cambia por la URL del front
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Sistema FashionVision AI Operativo",
        "fase": "Prototipo Inicial",
    }


@app.get("/api/test-detection")
async def test_detection():
    """Simulación del Sprint 7: Integración IA + Backend"""
    return {
        "status": "success",
        "data": {
            "prenda": "Vestido",
            "color": "Rojo",
            "confianza": 0.89,
            "sprint_objetivo": 7,
        },
    }
