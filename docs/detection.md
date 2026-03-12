# Detección de Prendas - FashionVision AI

## Descripción General

El sistema de detección de prendas utiliza **MobileNet**, un modelo de red neuronal convolucional (CNN) pre-entrenado optimizado para ejecutarse en dispositivos móviles y navegadores web.

### Tecnologías utilizadas

- **TensorFlow.js**: Biblioteca de JavaScript para ejecutar modelos de ML en el navegador
- **MobileNet**: Modelo pre-entrenado de Google para clasificación de imágenes

---

## Cómo Funciona la Detección

### Flujo de detección

```
1. Usuario captura foto con la cámara
   ↓
2. Imagen se procesa en elemento <canvas>
   ↓
3. Modelo MobileNet clasifica la imagen
   ↓
4. Se obtiene array de predicciones con:
   - className: categoría detectada (en inglés)
   - probability: confianza de 0 a 1
   ↓
5. traducirCategoria() traduce al español
   ↓
6. Se muestra resultado al usuario
```

### Archivo principal

`frontend/src/utils/imageProcessing.js` contiene la función `traducirCategoria()` que mapea las categorías del modelo a español.

---

## Categorías Disponibles

El modelo actualmente detecta las siguientes categorías:

| Clave (English) | Categoría (Español) |
|-----------------|---------------------|
| t-shirt         | Playera             |
| shirt           | Camisa              |
| jacket          | Chaqueta            |
| jean            | Pantalón            |
| dress           | Vestido             |
| shoe            | Zapato              |
| sneaker         | Zapatilla           |
| bag             | Bolsa               |
| hat             | Sombrero            |
| coat            | Abrigo              |
| sweater         | Suéter              |
| short           | Short               |
| suit            | Traje               |
| blazer          | Blazer              |
| skirt           | Falda               |
| hoodie          | Sudadera con capucha|
| cardigan        | Cárdigan            |
| polo            | Polo                |
| vest            | Chaleco             |
| legging         | Malla               |
| bikini          | Bikini              |
| bra             | Sujetador           |
| sock            | Calcetines          |
| glove           | Guante              |
| scarf           | Bufanda             |
| belt            | Cinturón            |
| watch           | Reloj               |
| handbag         | Bolso de mano       |
| wallet          | Billetera           |
| backpack        | Mochila             |
| briefcase       | Maletín             |
| luggage         | Equipaje            |

---

## Cómo Agregar Nuevas Categorías

### Paso 1: Editar el archivo de traducciones

Abre `frontend/src/utils/imageProcessing.js` y agrega tu nueva categoría al objeto `traducciones`:

```javascript
export const traducirCategoria = (texto) => {
  const traducciones = {
    // ... categorías existentes ...
    
    // Agregar nueva categoría aquí:
    'nueva_categoria': 'Mi Nueva Prenda',
  };

  const t = texto.toLowerCase();
  
  for (const [key, value] of Object.entries(traducciones)) {
    if (t.includes(key)) {
      return value;
    }
  }
  
  return texto;
};
```

### Paso 2: Consideraciones importantes

1. **Clave (key)**: Debe ser el nombre en inglés que MobileNet usa para esa categoría. Puedes encontrar los nombres completos en: https://github.com/tensorflow/tfjs-models/tree/master/mobilenet

2. **Valor (value)**: Puede ser cualquier texto en español que quieras mostrar

3. **Matching parcial**: El código usa `.includes()`, así que 'shirt' también coincidirá con "dress shirt" o "polo shirt"

### Paso 3: Verificar cambios

```bash
cd frontend
npm run lint
npm run build
```

---

## Cambiar el Modelo de Detección

Si deseas usar un modelo diferente:

### Opción 1: Usar otra versión de MobileNet

```javascript
// En frontend/src/hooks/useTensorFlow.js
import * as mobilenet from '@tensorflow-models/mobilenet';

// Cambiar versión
const modelo = await mobilenet.load({ version: 2, alpha: 1.0 });
```

Versiones disponibles:
- `version: 1` - MobileNet V1
- `version: 2` - MobileNet V2 (más preciso)

### Opción 2: Usar otro modelo

Puedes usar otros modelos de TensorFlow.js como:

- **Coco-SSD**: Detección de objetos múltiples
- **Teachable Machine**: Modelos personalizados
- **Custom TensorFlow**: Modelos entrenados específicamente

```javascript
// Ejemplo con otro modelo
import * as cocoSsd from '@tensorflow-models/coco-ssd';

const modelo = await cocoSsd.load();
const predicctions = await modelo.detect(imgElement);
```

---

## Limitaciones Actuales

1. **Solo detección de tipo**: Actualmente solo detecta el tipo de prenda, no colores ni otros atributos

2. **Modelo pre-entrenado**: MobileNet está entrenado con ImageNet, que tiene categorías limitadas de ropa

3. **Precisión**: La precisión depende de la calidad de la imagen y el ángulo de captura

---

## Recursos Adicionales

- [TensorFlow.js Documentation](https://www.tensorflow.org/js)
- [MobileNet Model](https://github.com/tensorflow/tfjs-models/tree/master/mobilenet)
- [ImageNet Categories](https://image-net.org/challenges/LSVRC/2012/browse-synsets)
