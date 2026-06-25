#!/usr/bin/env python3
"""
Exporta la especificación OpenAPI de FashionVision AI a un archivo JSON estático.

Uso:
    python scripts/export-openapi.py

Output:
    docs/api/openapi.json — Especificación completa de la API en formato OpenAPI 3.1

Requiere tener instaladas las dependencias del backend (pip install -r backend/requirements.txt).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.main import app

def export_openapi(output_path: str = "docs/api/openapi.json"):
    """Genera el archivo openapi.json desde la app FastAPI."""
    openapi_schema = app.openapi()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print(f"OpenAPI spec exported to {output_path}")
    print(f"  Paths: {len(openapi_schema.get('paths', {}))} endpoints")
    print(f"  Schemas: {len(openapi_schema.get('components', {}).get('schemas', {}))} schemas")

if __name__ == "__main__":
    export_openapi()
