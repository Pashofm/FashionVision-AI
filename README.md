# FashionVision AI
**Sistema Inteligente de Reconocimiento de Prendas y Análisis Predictivo**

FashionVision AI es una solución tecnológica diseñada para democratizar el uso de Inteligencia Artificial en pequeñas y medianas tiendas de ropa. [cite_start]El sistema automatiza el control de inventario y facilita el proceso de autocobro mediante visión por computadora (CNN) y análisis de datos. [cite: 1, 2, 12]

---

## Stack Tecnológico
- **Frontend:** React.js + CSS Moderno (Flexbox).
- **Backend:** Python 3.10+ con FastAPI.
- **Servidor Web:** Uvicorn.

---

## Instalación y Uso

Sigue estos pasos para ejecutar el prototipo en tu máquina local:

### 1. Requisitos Previos
- Node.js y npm instalados.
- Python 3.10 o superior instalado.

### 2. Configuración del Backend (Python)
Desde la terminal, en la raíz del proyecto:
```bash
# Entrar a la carpeta
cd backend

# Crear entorno virtual (Recomendado para Linux/Mac/Windows)
python -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
.\venv\Scripts\activate

# Instalar dependencias
pip install fastapi uvicorn

# Iniciar servidor
python -m uvicorn main:app --reload
```
