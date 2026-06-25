# ADR-001: PostgreSQL con pgvector como Base de Datos Unificada

**Estado:** Aceptado  
**Fecha:** 2024  
**Participantes:** Equipo de desarrollo

---

## Contexto

El sistema necesita almacenar tanto datos transaccionales (usuarios, productos, ventas, inventario) como datos vectoriales (embeddings de imágenes para matching visual con CLIP). Se evalúa si usar dos bases de datos separadas o una unificada.

## Opciones Consideradas

### Opción A: PostgreSQL + pgvector (unificada)
Una sola base de datos PostgreSQL con la extensión pgvector para operaciones vectoriales.

### Opción B: PostgreSQL + Pinecone/Weaviate (separadas)
PostgreSQL para datos transaccionales + un servicio externo especializado en vectores (Pinecone, Weaviate, Milvus).

### Opción C: PostgreSQL + almacenamiento en archivos
Embeddings guardados como archivos numpy y cargados en memoria al iniciar.

## Decisión

**Seleccionada: Opción A — PostgreSQL + pgvector**

## Justificación

1. **Simplicidad operacional**: Una sola base de datos que manejar, hacer backup y monitorear
2. **Consistencia transaccional**: Los embeddings se crean/eliminan en la misma transacción que las operaciones de producto, evitando problemas de sincronización
3. **Sin dependencia externa**: pgvector es una extensión nativa de PostgreSQL, sin servicios adicionales que mantener
4. **Rendimiento suficiente**: Para el volumen esperado (<10,000 productos), las búsquedas por similitud coseno en pgvector son más que adecuadas (índices IVFFlat)
5. **Costo**: Sin costos adicionales de servicios cloud para vectores

## Consecuencias

- Se requiere PostgreSQL 16+ con la extensión pgvector instalada
- La imagen Docker `pgvector/pgvector:pg16` incluye la extensión preinstalada
- Las búsquedas por similitud se hacen con el operador `<=>` (cosine distance) de pgvector
- El campo `embedding` en `product_embeddings` es de tipo `vector(512)` (512 dimensiones de CLIP ViT-B/32)
