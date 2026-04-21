# Guía de Instalación y Configuración - FashionVision-AI

Sistema completo para levantar y ejecutar FashionVision-AI.

---

## Selecciona tu Sistema Operativo

| Sistema | Archivo |
|---------|---------|
| Linux (Ubuntu, Debian, Fedora, Arch) | [INSTALACION_LINUX.md](./INSTALACION_LINUX.md) |
| Windows | [INSTALACION_WINDOWS.md](./INSTALACION_WINDOWS.md) |

---

## Resumen Rápido

### Linux

```bash
# 1. Clonar y entrar al proyecto
git clone https://github.com/tu-usuario/FashionVision-AI.git
cd FashionVision-AI

# 2. Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
sudo docker-compose up -d

# 3. Iniciar backend
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Frontend (en otra terminal)
cd frontend && npm install && npm run dev
```

### Windows

```powershell
# 1. Clonar y entrar al proyecto
git clone https://github.com/tu-usuario/FashionVision-AI.git
cd FashionVision-AI

# 2. Backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
docker-compose up -d

# 3. Iniciar backend
$env:PYTHONPATH = $PWD
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Frontend (en otra terminal)
cd frontend
npm install
npm run dev
```

---

## Puertos y Credenciales

| Servicio | Puerto | Credenciales |
|----------|--------|--------------|
| Backend API | 8000 | - |
| Frontend | 5173 | - |
| PostgreSQL | 5432 | fashionvision_ai_user / fashionvision_ai_pass |
| Login | - | admin@tienda.com / admin123 |

---

## URLs de Verificación

- **Backend**: http://localhost:8000
- **Swagger API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Frontend**: http://localhost:5173

---

## Guías Adicionales

- [INSTALACION_LINUX.md](./INSTALACION_LINUX.md) - Instalación completa para Linux
- [INSTALACION_WINDOWS.md](./INSTALACION_WINDOWS.md) - Instalación completa para Windows
- [GUIAS_PGADMIN.md](./GUIAS_PGADMIN.md) - Administrar base de datos visualmente
- [COMANDOS.md](./COMANDOS.md) - Comandos importantes del proyecto
