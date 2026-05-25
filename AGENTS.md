# Agent Guidelines for FashionVision-AI

React/Vite frontend + FastAPI backend for clothes detection using YOLO (Ultralytics).

## Project Structure

```
FashionVision-AI/
├── docker/              - Docker files (Dockerfiles, nginx.conf)
├── docker-compose.yml   - Docker orchestration
├── frontend/            - React 19 + Vite (port 5173)
├── backend/             - FastAPI with YOLO (port 8000)
├── docs/                - Documentation (DEVELOPMENT.md, etc.)
├── scripts/             - Helper scripts (dev-start.sh, etc.)
└── prueba-yolo/          - Legacy/alternate implementation
```

## Build/Lint/Test Commands

### Frontend (React + Vite)

```bash
cd frontend

# Install dependencies
npm install

# Development
npm run dev          # Start Vite dev server (http://localhost:5173)
npm run build        # Production build to dist/
npm run lint         # Run ESLint on all files
npm run preview      # Preview production build

# Single file lint with auto-fix
npx eslint src/pages/home.jsx --fix
```

### Backend (FastAPI + YOLO)

```bash
cd backend

# Setup
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run server (from project ROOT, NOT from backend folder)
cd /path/to/FashionVision-AI
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0
```

### Running Full Stack (Development Mode)

```bash
# Terminal 1 - Database (Docker)
docker compose up -d db

# Terminal 2 - Backend (local with hot-reload)
cd /path/to/FashionVision-AI
source backend/venv/bin/activate
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0

# Terminal 3 - Frontend (local)
cd frontend && npm run dev
```

### Running Full Stack (Docker Mode - Testing/Demo)

```bash
# Build and run everything in Docker
docker compose up -d --build

# Stop all services
docker compose down
```

## YOLO Detection

### Backend API Endpoints

- `POST /api/detect` - Upload image file for YOLO detection
- `GET /health` - Check if YOLO model is loaded
- `GET /` - Root endpoint

### Detection Flow

1. User captures image via camera
2. Frontend sends image to `/api/detect`
3. Backend runs YOLO inference
4. Returns detections with class, confidence, and bbox
5. Frontend draws green bounding boxes on canvas
6. Displays product info from database

### Trained Model

Location: `backend/models/best.pt`

**Current classes detected:** `gorra-roja-lacoste` (custom trained, 1 class)

### Product Database

Products with `yolo_class_name` are stored in the database and linked to YOLO detections:
- `gorra-roja-lacoste`: Gorra Roja Lacoste, $999.99, One Size

### Running Backend with YOLO Model

**Local development (IMPORTANT - set MODEL_PATH):**
```bash
cd /path/to/FashionVision-AI
source backend/venv/bin/activate
export PYTHONPATH=$PWD
export MODEL_PATH=$PWD/backend/models/best.pt
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0
```

**Docker (automatic - model is copied during build):**
```bash
docker compose up -d --build backend
```

### Dependencies Note

If running locally, ensure these packages are installed:
- `pytz==2024.1` (for timezone service)
- `torch==2.5.1` and `ultralytics==8.3.40` (for YOLO)
- `opencv-python-headless==4.10.0.84` (for image processing)

### YOLO Model Verification

After starting the backend, verify the model is loaded:
```bash
curl http://localhost:8000/api/detect/classes
# Should return: {"classes":{"0":"gorra-roja-lacoste"}}
```

## Code Style Guidelines

### JavaScript/React (Frontend)

**General**
- Use ES modules (`import`/`export`) - project uses `type: "module"` in package.json
- Prefer functional components with hooks
- Use `.jsx` for files with JSX, `.js` for utilities
- 2-space indentation, single quotes, semicolons at end of statements
- Trailing commas in multi-line objects/arrays, max ~100 chars per line

**Imports** - Order: React → external → internal → relative → CSS
```jsx
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import useCamera from '../hooks/useCamera';
import ButtonGroup from '../components/ButtonGroup';
import CameraSection from '../components/CameraSection';
import { detectClothes } from '../services/api';
import '../styles/home.css';
```

**Naming**
- Components: PascalCase (`UserProfile`, `ButtonGroup`)
- Hooks: camelCase with `use` prefix (`useCamera`)
- API services: camelCase (`detectClothes`, `checkHealth`)
- Files: kebab-case for services/utils, PascalCase.jsx for components

**Error Handling**
- Use try/catch for async operations
- Set error state: `setAppError('Descripción del error')`
- Log with `console.error()`

**React Patterns**
- Destructure props: `function Component({ title, children })`
- Early returns: `if (!isActive) return null`
- Keep components small and focused

### ESLint Configuration

Uses flat config (`eslint.config.js`):
- `@eslint/js`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`
- Custom rule: `no-unused-vars` ignores vars starting with uppercase (JSX components)

### Python (Backend)

- Follow PEP 8 style guide, 4-space indentation
- Use type hints, snake_case for functions/variables
- PascalCase for classes, UPPER_SNAKE_CASE for constants

## File Organization

```
frontend/src/
├── App.jsx            # Root component with routing
├── main.jsx           # Entry point
├── components/        # Reusable UI (ButtonGroup.jsx, CameraSection.jsx)
├── pages/             # Route pages (Dashboard.jsx, home.jsx, login.jsx)
├── hooks/             # Custom hooks (useCamera.js)
├── services/          # API services (api.js)
└── styles/           # Stylesheets (home.css, login.css)

backend/
├── main.py            # FastAPI application with YOLO endpoints
├── app/main.py        # Alternative structure
├── models/            # Trained YOLO weights (best.pt)
└── requirements.txt   # Python dependencies
```

## Key Technologies

### Frontend
- React 19.2.0, React Router DOM 7.13.2, Recharts 3.8.1
- Vite 7.3.1, ESLint 9.39.1

### Backend
- FastAPI, Uvicorn
- Ultralytics YOLO (YOLOv11/YOLOv8)
- Torch 2.5.1, Pillow, OpenCV
- Cloudinary SDK for image uploads

## Environment Variables

Create `.env.local` in frontend:
- `VITE_API_URL` - Backend API endpoint (default: http://localhost:8000)
- Variables must be prefixed with `VITE_`

### Cloudinary Configuration

Cloudinary is used for product image storage. Configure in `.env`:
```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

**API Endpoints for Images:**
- `POST /api/products/{product_id}/images` - Upload image to product
- `DELETE /api/products/{product_id}/images` - Remove product image

## API Integration

- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:5173 (dev) or http://localhost (Docker)
- CORS configured to allow frontend access

### Frontend API Service (`src/services/api.js`)

```javascript
import { detectClothes, checkHealth } from '../services/api';

// Detect clothes in image
const result = await detectClothes(imageFile);
// Returns: { detections: [{class, confidence, bbox}], image_size }

// Check backend health
const status = await checkHealth();
// Returns: { status: 'healthy', database: 'connected', model_loaded: true }
```

## Docker Deployment

### Services (via docker-compose.yml)

| Service | Port | Description |
|---------|------|-------------|
| frontend | 80 | Nginx serving React build |
| backend | 8000 | FastAPI + YOLO |
| db | 5432 | PostgreSQL 16 |

### Helper Scripts

```bash
# Development mode (DB + local backend + local frontend)
./scripts/dev-start.sh

# Stop development services
./scripts/dev-stop.sh

# Everything in Docker (testing/demo)
./scripts/docker-start.sh

# Reset database (WARNING: deletes data)
./scripts/db-reset.sh
```

### Quick Docker Commands

```bash
# Start everything
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f backend

# Rebuild (after requirements.txt changes)
docker compose build --no-cache backend
docker compose up -d backend

# Full reset
docker compose down -v
docker compose up -d
```

## YOLO Model Verification

After starting the backend, verify the model is loaded:
```bash
curl http://localhost:8000/api/detect/classes
# Should return: {"classes":{"0":"gorra-roja-lacoste"}}
```
