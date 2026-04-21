# Guía para Gestionar Dataset YOLO y Productos

Documentación completa para agregar nuevas clases al modelo YOLO y gestionar productos en la base de datos.

---

## Tabla de Contenidos

1. [Estructura del Sistema de Detección](#1-estructura-del-sistema-de-detección)
2. [Agregar Nuevas Clases al Dataset](#2-agregar-nuevas-clases-al-dataset)
3. [Entrenar el Modelo YOLO](#3-entrenar-el-modelo-yolo)
4. [Actualizar el Modelo en el Backend](#4-actualizar-el-modelo-en-el-backend)
5. [Agregar Productos a la Base de Datos](#5-agregar-productos-a-la-base-de-datos)
6. [Mapear Clases YOLO a Productos](#6-mapear-clases-yolo-a-productos)
7. [Comandos de Referencia](#7-comandos-de-referencia)

---

## 1. Estructura del Sistema de Detección

### Flujo de Detección

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Cámara    │────▶│  Backend     │────▶│   Frontend   │
│  (Cliente)  │     │  /api/detect│     │  /detection │
└──────────────┘     └──────────────┘     └──────────────┘
                           │
                           ▼
                     ┌──────────────┐
                     │  YOLO Model  │
                     │  best.pt     │
                     └──────────────┘
```

### Archivos Involucrados

| Archivo/Directorio | Descripción |
|-------------------|--------------|
| `backend/models/best.pt` | Modelo YOLO entrenado |
| `backend/app/services/detection.py` | Servicio de detección |
| `prueba-yolo/backend/prueba2-1/` | Dataset original |
| Base de datos PostgreSQL | Productos |

### Clases Actualmente Entrenadas

| Clase YOLO | Producto |
|------------|----------|
| `gorra-roja-lacoste` | Gorra Roja Lacoste ($999.99) |

---

## 2. Agregar Nuevas Clases al Dataset

### Paso 2.1: Preparar Imágenes

1. **Crear carpeta para el dataset** (si no existe):
```bash
mkdir -p backend/prueba2-1/train/images
mkdir -p backend/prueba2-1/train/labels
mkdir -p backend/prueba2-1/valid/images
mkdir -p backend/prueba2-1/valid/labels
mkdir -p backend/prueba2-1/test/images
```

2. **Agregar imágenes de entrenamiento**:
   - Mínimo recomendado: 10-20 imágenes por clase
   - Formato: JPG o PNG
   - Resolución recomendada: 640x640 o superior
   - Nombres sugeridos: `nombre_producto_001.jpg`, `nombre_producto_002.jpg`

3. **Agregar imágenes de validación**:
   - Mínimo: 3-5 imágenes por clase
   - Separadas de training para evaluar el modelo

### Paso 2.2: Anotar Imágenes con LabelImg

1. **Instalar labelImg** (si no está instalado):
```bash
# Linux
pip install labelImg

# Windows
pip install labelImg
```

2. **Ejecutar labelImg**:
```bash
labelImg backend/prueba2-1/train/images
```

3. **Configurar clases en labelImg**:
   - Click en "Change Save Dir" → seleccionar `backend/prueba2-1/train/labels`
   - Click en "Change Predefined Classes" → agregar clases
   - Click en "View" → "Auto Save Mode"

4. **Anotar**:
   - Draw rectangle around the clothing item
   - Select/enter class name
   - Press "Next Image" or "w" ( shortcut)
   - Save automatically when auto save is enabled

### Paso 2.3: Formato de Etiquetas YOLO

El archivo `.txt` generado debe tener este formato:
```
<class_id> <x_center> <y_center> <width> <height>
```

- `class_id`: Índice de la clase (0, 1, 2, ...)
- Las coordenadas están normalizadas (0-1)

**Ejemplo** (`gorra1.txt`):
```
0 0.5 0.3 0.2 0.15
```
Significa: clase 0 (gorra-roja-lacoste), centro en 50%X, 30%Y, ancho 20%, alto 15%

### Paso 2.4: Actualizar data.yaml

Editar `backend/prueba2-1/data.yaml`:
```yaml
names:
  - gorra-roja-lacoste
  - top
  - pants
  - nueva-prenda

nc: 4

train: train/images
val: valid/images
test: test/images
```

---

## 3. Entrenar el Modelo YOLO

### Paso 3.1: Instalar Dependencias

```bash
cd backend
source venv/bin/activate
pip install ultralytics torch
```

### Paso 3.2: Script de Entrenamiento

Crear `backend/train_model.py`:

```python
#!/usr/bin/env python3
"""Script para entrenar modelo YOLO con el dataset."""

from ultralytics import YOLO
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "prueba2-1", "data.yaml")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "best.pt")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "models")

def train_model(epochs=50, imgsz=640):
    # Cargar modelo pre-entrenado
    model = YOLO("yolo11n.pt")
    
    # Entrenar
    results = model.train(
        data=DATA_PATH,
        epochs=epochs,
        imgsz=imgsz,
        batch=8,
        project=OUTPUT_DIR,
        name="clothes_detector",
        exist_ok=True,
        verbose=True,
        workers=0,
    )
    
    print(f"mAP50: {results.results_dict.get('metrics/mAP50(B)', 0):.3f}")
    print(f"mAP50-95: {results.results_dict.get('metrics/mAP50-95(B)', 0):.3f}")
    
    return results

if __name__ == "__main__":
    train_model()
```

### Paso 3.3: Ejecutar Entrenamiento

```bash
cd backend
source venv/bin/activate
python train_model.py
```

**Tiempo estimado**:
- 50 epochs con GPU: ~10-30 minutos
- 50 epochs con CPU: ~2-4 horas

### Paso 3.4: Ver Resultados

El modelo entrenado se guarda en:
```
backend/models/clothes_detector/weights/
├── best.pt      # Mejor modelo según mAP
└── last.pt      # Último checkpoint
```

Ver métricas en:
```
backend/models/clothes_detector/results.csv
backend/models/clothes_detector/results.png
```

---

## 4. Actualizar el Modelo en el Backend

### Paso 4.1: Copiar Modelo Entrenado

```bash
# Copiar best.pt a la carpeta de modelos del backend
cp backend/models/clothes_detector/weights/best.pt backend/models/best.pt

# O si prefieres usar last.pt:
# cp backend/models/clothes_detector/weights/last.pt backend/models/best.pt
```

### Paso 4.2: Reiniciar el Backend

```bash
# Matar proceso existente
pkill -f uvicorn

# Reiniciar
cd /ruta/al/proyecto
source backend/venv/bin/activate
PYTHONPATH=. uvicorn backend.app.main:app --port 8000 --reload
```

### Paso 4.3: Verificar Clases Cargadas

```bash
curl http://localhost:8000/api/detect/classes
```

**Respuesta esperada**:
```json
{
  "classes": {
    "0": "gorra-roja-lacoste",
    "1": "top",
    "2": "pants",
    "3": "nueva-prenda"
  }
}
```

---

## 5. Agregar Productos a la Base de Datos

### Opción A: Via pgAdmin

1. **Abrir pgAdmin** → http://localhost:5050
2. **Navegar**: Servers → FashionVision DB → Databases → fashionvision_ai → Schemas → public → Tables → products
3. **Click derecho en products** → "View/Edit Data" → "All Rows"
4. **Agregar fila** con los datos del producto

### Opción B: Via SQL (psql o pgAdmin Query Tool)

```sql
-- Insertar nuevo producto
INSERT INTO products (
    category_id, 
    name, 
    sku, 
    base_price, 
    yolo_class_id,
    yolo_class_name,
    description,
    is_active
) VALUES (
    'c0000001-0000-0000-0000-000000000001',  -- category_id (verificar en categories)
    'Playera Básica Blanca',                    -- name
    'PLAY-BAS-001',                            -- sku (debe ser único)
    180.00,                                    -- base_price
    3,                                         -- yolo_class_id (debe coincidir con modelo)
    'top',                                     -- yolo_class_name (nombre de la clase YOLO)
    'Playera básica de algodón 100%',         -- description
    true                                       -- is_active
);
```

### Opción C: Via API REST

```bash
# Login primero
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@tienda.com","password":"admin123"}' | jq -r '.access_token')

# Crear producto
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "category_id": "c0000001-0000-0000-0000-000000000001",
    "name": "Playera Básica Blanca",
    "sku": "PLAY-BAS-001",
    "base_price": 180.00,
    "yolo_class_id": 3,
    "yolo_class_name": "top",
    "description": "Playera básica de algodón 100%"
  }'
```

### Estructura de la Tabla Products

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador único (auto-generado) |
| `category_id` | UUID | FK a categories |
| `name` | VARCHAR(200) | Nombre del producto |
| `sku` | VARCHAR(100) | Código único del producto |
| `base_price` | DECIMAL(10,2) | Precio base |
| `yolo_class_id` | INTEGER | Índice de clase en modelo YOLO |
| `yolo_class_name` | VARCHAR(100) | Nombre de la clase YOLO |
| `description` | TEXT | Descripción opcional |
| `images` | JSONB | URLs de imágenes |
| `is_active` | BOOLEAN | Si está activo |
| `created_at` | TIMESTAMP | Fecha de creación |

---

## 6. Mapear Clases YOLO a Productos

### Sistema de Mapeo

El frontend (`ClientDetection.jsx`) tiene un mapeo hardcodeado:

```javascript
const DATASET_PRODUCTS = {
  'gorra-roja-lacoste': {
    name: 'Gorra Roja Lacoste',
    price: 999.99,
    brand: 'Lacoste',
    sku: 'GOR-001',
    sizes: ['One Size'],
    colors: ['Rojo'],
    tipoPrenda: 'Gorra'
  },
  'top': {
    name: 'Camiseta Algodon',
    price: 299.99,
    brand: 'FashionCo',
    sku: 'CAM-001',
    sizes: ['S', 'M', 'L', 'XL'],
    colors: ['Blanco', 'Negro'],
    tipoPrenda: 'Camiseta'
  },
  // ... más productos
};
```

### Para Actualizar el Mapeo

1. **Abrir** `frontend/src/pages/ClientDetection.jsx`
2. **Buscar** `DATASET_PRODUCTS`
3. **Agregar/Modificar** entrada:

```javascript
'nueva-prenda': {
  name: 'Nombre del Producto',
  price: 599.99,
  brand: 'Marca',
  sku: 'SKU-001',
  sizes: ['S', 'M', 'L', 'XL'],
  colors: ['Rojo', 'Azul'],
  tipoPrenda: 'Tipo de Prenda'
}
```

4. **Guardar** y el frontend se actualiza automáticamente (si `--reload` está activo)

---

## 7. Comandos de Referencia

### Docker

```bash
# Iniciar base de datos
cd backend && docker-compose up -d

# Ver contenedores
docker ps

# Ver logs
docker logs -f fashionvision_db

# Acceder a psql
docker exec -it fashionvision_db psql -U fashionvision_ai_user -d fashionvision_ai
```

### Backend

```bash
# Activar entorno
cd backend && source venv/bin/activate

# Iniciar servidor
cd /ruta/al/proyecto
PYTHONPATH=. uvicorn backend.app.main:app --port 8000 --reload

# Verificar clases del modelo
curl http://localhost:8000/api/detect/classes

# Probar detección
curl -X POST http://localhost:8000/api/detect \
  -F "file@/ruta/a/imagen.jpg"
```

### Entrenamiento

```bash
# Entrenar modelo (desde backend/)
python train_model.py

# Ver modelo entrenado
ls -la models/clothes_detector/weights/
```

### Base de Datos

```sql
-- Ver categorías
SELECT * FROM categories;

-- Ver productos
SELECT id, name, sku, yolo_class_name, base_price FROM products;

-- Insertar producto
INSERT INTO products (category_id, name, sku, base_price, yolo_class_id, yolo_class_name)
VALUES ('uuid-categoria', 'Nombre', 'SKU-001', 99.99, 0, 'nombre-clase');

-- Ver productos con categorías
SELECT p.name, p.sku, c.name as category, p.base_price
FROM products p
JOIN categories c ON p.category_id = c.id;
```

### pgAdmin

```bash
# Acceso
http://localhost:5050
Email: admin@fashionvision.com
Password: admin123

# Agregar servidor
Host: host.docker.internal
Port: 5433
Database: fashionvision_ai
Username: fashionvision_ai_user
Password: fashionvision_ai_pass
```

---

## Checklist para Agregar Nueva Prenda

- [ ] 1. Recopilar 10-20 imágenes de la nueva prenda
- [ ] 2. Anotar imágenes con labelImg
- [ ] 3. Actualizar data.yaml con nueva clase
- [ ] 4. Entrenar modelo YOLO
- [ ] 5. Copiar best.pt a backend/models/
- [ ] 6. Reiniciar backend
- [ ] 7. Verificar clases con `/api/detect/classes`
- [ ] 8. Agregar producto a base de datos
- [ ] 9. Actualizar DATASET_PRODUCTS en ClientDetection.jsx
- [ ] 10. Probar detección completa

---

## Solución de Problemas

### Error "Model not found"

```bash
# Verificar que el modelo existe
ls -la backend/models/best.pt

# Si no existe, copiar desde entrenado
cp backend/models/clothes_detector/weights/best.pt backend/models/best.pt
```

### Error "No detections"

- Verificar que la imagen es clara y la prenda está visible
- Bajar el threshold de confianza en `detection.py`:
```python
def detect_in_image(image, conf_threshold=0.05):  # bajar de 0.25 a 0.05
```

### Error de conexión a base de datos

```bash
# Verificar que PostgreSQL está corriendo
docker ps

# Reiniciar
docker-compose restart
```

---

## Próximos Pasos

Después de agregar nuevas prendas:

1. **Integrar con carrito** - Conectar detección con sistema de carrito existente
2. **Optimizar modelo** - Más datos de entrenamiento para mejor precisión
3. **Multi-detección** - Detectar múltiples prendas en una sola imagen
