# ADR-002: Pipeline de Visión YOLO + CLIP

**Estado:** Aceptado  
**Fecha:** 2024  
**Participantes:** Equipo de desarrollo

---

## Contexto

El sistema debe detectar prendas de vestir en imágenes capturadas por la cámara del kiosko y luego encontrar el producto correspondiente en el catálogo. Se necesita definir la arquitectura del pipeline de visión por computadora.

## Opciones Consideradas

### Opción A: YOLO para detección + CLIP para matching
YOLO detecta las prendas y sus bounding boxes. CLIP genera embeddings de los crops detectados y los compara con embeddings pre-calculados de los productos del catálogo.

### Opción B: Solo YOLO con clases predefinidas
YOLO clasifica la prenda en una categoría (ej: "camiseta", "pantalón") y se busca por categoría en el catálogo sin matching visual.

### Opción C: Modelo único multi-tarea
Un solo modelo que detecta, clasifica y asigna un product_id directamente.

## Decisión

**Seleccionada: Opción A — YOLO + CLIP**

## Justificación

1. **Separación de responsabilidades**: Detección y matching son problemas distintos que se benefician de modelos especializados
2. **Precisión de matching**: CLIP ofrece matching visual por similitud, más preciso que buscar solo por categoría (especialmente útil para productos visualmente similares pero de distintas marcas/precios)
3. **Flexibilidad**: Se pueden agregar nuevos productos al catálogo sin reentrenar YOLO — solo se genera su embedding CLIP
4. **Modelos pre-entrenados**: Tanto YOLO como CLIP tienen modelos pre-entrenados de alta calidad que funcionan con fine-tuning mínimo
5. **Escalabilidad**: El catálogo puede crecer sin degradar el rendimiento del matching

## Pipeline

```
Imagen → YOLO (detección) → Crop de prenda → CLIP (embedding) → Cosine similarity vs BD → Producto más similar
```

## Consecuencias

- Se requiere GPU o CPU suficiente para correr ambos modelos (YOLO + CLIP)
- El tiempo de inferencia combinado es aceptable (~1-3 segundos en CPU, <500ms en GPU)
- Los embeddings de productos se pre-calculan al subir imágenes (no en tiempo de inferencia)
- El modelo YOLO usa pesos personalizados (`best.pt`) fine-tuneados para prendas de vestir
- CLIP usa el modelo ViT-B/32 (512 dimensiones), buen balance precisión/rendimiento
