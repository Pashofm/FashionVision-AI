# Guía de Contribución

Gracias por tu interés en contribuir a FashionVision AI. Este documento describe las pautas para colaborar en el proyecto.

---

## Código de Conducta

Este proyecto sigue un código de conducta basado en el respeto mutuo. Sé amable, constructivo y profesional en todas las interacciones.

---

## Cómo Contribuir

### Reportar Bugs

1. Revisa los [issues existentes](https://github.com/Pashofm/FashionVision-AI/issues) para evitar duplicados
2. Usa la plantilla de **Bug Report** al crear un nuevo issue
3. Incluye pasos para reproducir, comportamiento esperado vs real, y capturas si aplica

### Sugerir Funcionalidades

1. Usa la plantilla de **Feature Request**
2. Describe el problema que resuelve y la solución propuesta
3. Si es un cambio grande, abre un issue de discusión primero

### Pull Requests

1. Haz fork del repositorio y crea una rama desde `main`
2. Nombra la rama según el tipo: `feature/descripcion`, `fix/descripcion`, `docs/descripcion`
3. Sigue las convenciones de código del proyecto
4. Asegúrate de que los tests pasen
5. Actualiza la documentación si tu cambio lo requiere
6. Usa la plantilla de Pull Request

---

## Convenciones de Código

### Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```
tipo(ámbito): descripción breve

- feat: nueva funcionalidad
- fix: corrección de bug
- docs: cambios en documentación
- refactor: refactorización sin cambios funcionales
- test: cambios en tests
- chore: tareas de mantenimiento
```

### Backend (Python)

- Sigue [PEP 8](https://peps.python.org/pep-0008/)
- Usa type hints en funciones públicas
- Escribe docstrings para módulos, clases y funciones públicas
- Organiza imports: estándar → terceros → locales

### Frontend (React)

- Usa componentes funcionales con hooks
- Nombra componentes en PascalCase, archivos en PascalCase
- Mantén los estilos en archivos CSS separados por página
- Usa los servicios existentes para llamadas a la API

### Base de Datos

- Los cambios de esquema se hacen vía migraciones Alembic
- No modifiques `schema.sql` directamente — genera migraciones
- Actualiza `seed.sql` si agregas datos semilla

---

## Entorno de Desarrollo

Sigue la [Guía de Instalación](docs/INSTALLATION.md) para configurar tu entorno.

### Modos de trabajo

| Modo | Comando | Descripción |
|------|---------|-------------|
| Hot-reload | `./scripts/dev-start.sh` | Ideal para desarrollo frontend/backend |
| Docker full | `./scripts/docker-start.sh` | Entorno completo con BD, pgAdmin |

### Ejecutar Tests

```bash
# Backend
cd backend
python -m pytest tests/ -v

# Frontend
cd frontend
npm run test:run

# Con scripts
./backend/scripts/run_tests.sh
```

---

## Estructura del Proyecto

```
FashionVision-AI/
├── backend/           # API FastAPI + SQLAlchemy
│   ├── app/           # Código de la aplicación
│   ├── alembic/       # Migraciones de BD
│   ├── database/      # Schema SQL y seed data
│   ├── tests/         # Tests unitarios e integración
│   └── scripts/       # Scripts de BD de testing
├── frontend/          # React 19 + Vite
│   └── src/
│       ├── components/ # Componentes reutilizables
│       ├── contexts/   # Contextos de React
│       ├── hooks/      # Hooks personalizados
│       ├── pages/      # Páginas de la app
│       ├── services/   # Clientes de API
│       └── styles/     # Hojas de estilo
├── docker/            # Dockerfiles y configs
├── docs/              # Documentación del proyecto
├── scripts/           # Scripts de automatización
└── docker-compose.yml
```

---

## Documentación

La documentación vive en `docs/`. Si agregas una funcionalidad nueva:

1. Crea o actualiza el archivo de documentación correspondiente
2. Actualiza el `CHANGELOG.md` en la sección `[Unreleased]`
3. Si es relevante, actualiza el `README.md`

---

## Preguntas

Si tienes dudas, abre un issue con la etiqueta `question` o contacta al equipo mantenedor.
