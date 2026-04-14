# FashionVision AI

**Sistema Inteligente de Reconocimiento de Prendas y Análisis Predictivo**

FashionVision AI es una solución tecnológica diseñada para democratizar el uso de Inteligencia Artificial en pequeñas y medianas tiendas de ropa. El sistema automatiza el control de inventario y facilita el proceso de autocobro mediante visión por computadora (YOLO) y análisis de datos.

---

## Stack Tecnológico

- **Frontend:** React 19 + Vite + CSS Moderno
- **Backend:** Python 3.10+ con FastAPI
- **Modelo de IA:** YOLO (Ultralytics) para detección de prendas
- **Servidor Web:** Uvicorn

---

## Características

- **Detección de prendas** con YOLO: Identifica prendas de vestir en tiempo real
- **Bounding boxes verdes** sobre las prendas detectadas
- **Base de datos de productos**: Información detallada de cada prenda (precio, marca, tallas, colores)
- **Detección de color**: Analiza el color dominante de la prenda
- **Interfaz moderna** con React y CSS gradient

---

## Instalación y Uso

### 1. Requisitos Previos

- Node.js y npm instalados
- Python 3.10 o superior instalado

### 2. Configuración del Backend (Python)

```bash
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
uvicorn main:app --reload --port 8000
```

El backend estará corriendo en: **http://localhost:8000**

### 3. Configuración del Frontend (Vite + React)

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar entorno de desarrollo
npm run dev
```

El frontend estará disponible en: **http://localhost:5173**

---

## Uso

1. Abre el navegador en **http://localhost:5173**
2. Haz clic en **"Abrir Cámara"**
3. Apunta la cámara a una prenda (gorra roja Lacoste, camiseta o pantalón)
4. Presiona **"Capturar"**
5. Visualiza:
   - Imagen con bounding box verde
   - Información del producto detectado
   - Precio, marca, tallas disponibles
   - Porcentaje de confianza

---

## Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Endpoint raíz |
| GET | `/health` | Estado del servidor y modelo |
| POST | `/api/detect` | Detectar prendas en imagen |

### Detección de Prendas

```bash
curl -X POST "http://localhost:8000/api/detect" \
  -F "file=@imagen.jpg"
```

**Respuesta:**
```json
{
  "detections": [
    {
      "class": "gorra-roja-lacoste",
      "confidence": 0.95,
      "bbox": [x1, y1, x2, y2]
    }
  ],
  "image_size": [640, 480]
}
```

---

## Productos Detectables

| Clase YOLO | Producto | Precio |
|------------|----------|--------|
| `gorra-roja-lacoste` | Gorra Roja Lacoste | $999.99 |
| `top` | Camiseta Algodon | $299.99 |
| `pants` | Jean Slim Fit | $599.99 |

---

## Modelo YOLO

- **Ubicación:** `backend/models/best.pt`
- **Framework:** Ultralytics YOLO
- **Entrenamiento:** Dataset personalizado de prendas de ropa

Para entrenar con nuevas clases, consulta `prueba-yolo/backend/train.py`.

---

## Comandos de Desarrollo

```bash
# Frontend
cd frontend
npm run dev          # Desarrollo
npm run build        # Build producción
npm run lint         # ESLint

# Backend
cd backend
uvicorn main:app --reload --port 8000

# Linting single file
npx eslint src/pages/home.jsx --fix
```

---

## Estructura del Proyecto

```
FashionVision-AI/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── home.jsx          # Página de detección principal
│   │   │   ├── Dashboard.jsx     # Dashboard con gráficos
│   │   │   └── login.jsx         # Página de login
│   │   ├── components/
│   │   │   ├── ButtonGroup.jsx   # Botones de acción
│   │   │   └── CameraSection.jsx # Sección de cámara
│   │   ├── hooks/
│   │   │   └── useCamera.js      # Hook para cámara
│   │   ├── services/
│   │   │   └── api.js            # Cliente API
│   │   └── styles/
│   │       └── home.css          # Estilos de detección
│   └── package.json
│
├── backend/
│   ├── main.py                   # FastAPI con endpoints YOLO
│   ├── models/
│   │   └── best.pt              # Modelo entrenado
│   └── requirements.txt
│
├── docs/
│   └── detection.md             # Documentación de detección
│
└── prueba-yolo/                 # Implementación alternativa legacy
```
