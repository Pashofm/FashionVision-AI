# Detección de Prendas - FashionVision AI

## Descripción General

El sistema de detección de prendas utiliza **YOLO** (You Only Look Once), un modelo de detección de objetos en tiempo real desarrollado por Ultralytics.

### Tecnologías utilizadas

- **FastAPI**: Framework web para el backend
- **Ultralytics YOLO**: Modelo de detección de objetos
- **Pillow/OpenCV**: Procesamiento de imágenes

---

## Cómo Funciona la Detección

### Flujo de detección

```
1. Usuario abre la cámara
   ↓
2. Captura una foto de la prenda
   ↓
3. Imagen se envía al backend via POST /api/detect
   ↓
4. YOLO procesa la imagen y detecta objetos
   ↓
5. Backend retorna detecciones con:
   - class: categoría detectada
   - confidence: confianza de 0 a 1
   - bbox: coordenadas del bounding box [x1, y1, x2, y2]
   ↓
6. Frontend dibuja bounding boxes verdes en canvas
   ↓
7. Se muestra información del producto
```

### Archivos principales

- `backend/main.py` - Servidor FastAPI con endpoint de detección
- `frontend/src/pages/home.jsx` - Componente de detección
- `frontend/src/services/api.js` - Cliente API
- `frontend/src/hooks/useCamera.js` - Hook para cámara

---

## Endpoint de Detección

### POST `/api/detect`

Envía una imagen y recibe las detecciones.

**Request:**
```
Content-Type: multipart/form-data
Body: file (imagen)
```

**Response:**
```json
{
  "detections": [
    {
      "class": "gorra-roja-lacoste",
      "confidence": 0.95,
      "bbox": [120, 80, 340, 200]
    }
  ],
  "image_size": [640, 480]
}
```

**Códigos de respuesta:**
- 200: Detección exitosa
- 500: Error en el servidor

---

## Clases Disponibles

El modelo actualmente detecta las siguientes clases:

| Clase (YOLO) | Producto | Precio | Marca |
|--------------|----------|--------|-------|
| gorra-roja-lacoste | Gorra Roja Lacoste | $999.99 | Lacoste |
| top | Camiseta Algodon | $299.99 | FashionCo |
| pants | Jean Slim Fit | $599.99 | DenimCraft |

---

## Agregar Nuevas Clases

### Paso 1: Entrenar nuevo modelo

```bash
cd prueba-yolo/backend

# Editar data.yaml con las nuevas clases
# Entrenar modelo
python train.py
```

### Paso 2: Actualizar el modelo

Copiar el nuevo modelo:
```bash
cp models/clothes_detector/weights/best.pt ../../backend/models/best.pt
```

### Paso 3: Agregar producto a la base de datos

En `frontend/src/pages/home.jsx`, agregar al objeto `PRODUCTOS_DB`:

```javascript
const PRODUCTOS_DB = {
  'nueva-clase': {
    name: 'Nombre del Producto',
    price: 299.99,
    brand: 'Marca',
    sku: 'PROD-001',
    sizes: ['S', 'M', 'L'],
    colors: ['Blanco', 'Negro'],
    tipoPrenda: 'Tipo de Prenda'
  },
  // ... otras clases
};
```

---

## Cómo se Dibujan los Bounding Boxes

El frontend dibuja los bounding boxes usando Canvas API:

```javascript
// En home.jsx, useEffect que dibuja las cajas
useEffect(() => {
  if (imagen && detections && resultCanvasRef.current) {
    const canvas = resultCanvasRef.current;
    const ctx = canvas.getContext('2d');
    
    detections.forEach((det) => {
      const [x1, y1, x2, y2] = det.bbox;
      
      // Dibujar rectángulo verde
      ctx.strokeStyle = '#00ff00';
      ctx.lineWidth = 3;
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
      
      // Dibujar texto con clase y confianza
      ctx.fillStyle = '#00ff00';
      ctx.font = 'bold 16px sans-serif';
      ctx.fillText(`${det.class} ${Math.round(det.confidence * 100)}%`, x1, y1 - 8);
    });
  }
}, [imagen, detections]);
```

---

## Detección de Color

Además de YOLO, el sistema detecta el color dominante de la prenda:

```javascript
const detectarColor = (canvas) => {
  // Analiza los píxeles de la imagen
  // Retorna: 'Rojo', 'Verde', 'Azul', 'Blanco', 'Negro', o 'Color mixto'
};
```

---

## Limitaciones Actuales

1. **Modelo específico**: El modelo está entrenado solo con 3 clases de prendas
2. **Precisión variable**: La confianza depende de la calidad de la imagen y ángulo
3. **Un objeto por imagen**: El sistema muestra información del primer objeto detectado

---

## Recursos Adicionales

- [Ultralytics YOLO Documentation](https://docs.ultralytics.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [YOLO Training Guide](https://docs.ultralytics.com/datasets/detect/)
