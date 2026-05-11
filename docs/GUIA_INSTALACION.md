# Guía de Instalación y Configuración - FashionVision-AI

Sistema completo para levantar y ejecutar FashionVision-AI.

---

## Selecciona tu Sistema Operativo

| Sistema | Archivo |
|---------|---------|
| Linux (Ubuntu, Debian, Fedora, Arch) | [INSTALACION_LINUX.md](./INSTALACION_LINUX.md) |
| Windows (PowerShell/CMD) | [INSTALACION_WINDOWS.md](./INSTALACION_WINDOWS.md) |
| Windows + WSL2 (Recomendado) | [WINDOWS_WSL2.md](./WINDOWS_WSL2.md) |
| macOS (Homebrew) | [INSTALACION_MACOS.md](./INSTALACION_MACOS.md) |

---

## Resumen Rápido

### Linux

```bash
# 1. Clonar y entrar al proyecto
git clone https://github.com/tu-usuario/FashionVision-AI.git
cd FashionVision-AI

# 2. Setup inicial (recomendado)
./scripts/setup.sh

# 3. Editar .env con credenciales
nano .env

# 4. Iniciar servicios
./scripts/deploy-local.sh
```

### macOS

```bash
# 1. Clonar y entrar al proyecto
git clone https://github.com/tu-usuario/FashionVision-AI.git
cd FashionVision-AI

# 2. Setup inicial
./scripts/setup.sh

# 3. Editar .env con credenciales
nano .env

# 4. Iniciar servicios
./scripts/deploy-local.sh
```

### Windows + WSL2 (Recomendado)

```bash
# En WSL2 terminal
git clone https://github.com/tu-usuario/FashionVision-AI.git
cd FashionVision-AI
./scripts/setup.sh
nano .env  # Editar credenciales
./scripts/deploy-local.sh
```

### Windows (Nativo PowerShell)

```powershell
# 1. Clonar y entrar al proyecto
git clone https://github.com/tu-usuario/FashionVision-AI.git
cd FashionVision-AI

# 2. Backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# 3. Iniciar base de datos
docker compose up -d db

# 4. Iniciar backend
$env:PYTHONPATH = $PWD
alembic upgrade head
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Frontend (en otra terminal)
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
| PostgreSQL | 5432 | (del .env) |
| pgAdmin | 5050 | (del .env) |
| Login por defecto | - | admin@tienda.com / admin123 |

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
- [WINDOWS_WSL2.md](./WINDOWS_WSL2.md) - Windows + WSL2 + Docker Desktop
- [INSTALACION_MACOS.md](./INSTALACION_MACOS.md) - Instalación para macOS
- [GUIAS_PGADMIN.md](./GUIAS_PGADMIN.md) - Administrar base de datos visualmente
- [COMANDOS.md](./COMANDOS.md) - Comandos importantes del proyecto
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Despliegue a producción
- [scripts/README.md](../scripts/README.md) - Documentación de scripts
