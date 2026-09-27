.PHONY: help up up-build down logs logs-backend logs-db logs-frontend logs-nginx \
        shell-backend shell-db migrate migrate-status migrate-history migrate-down \
        seed test-backend test-frontend clean

help: ## Mostrar esta ayuda
	@echo "FashionVision AI — Comandos disponibles"
	@echo "========================================"
	@echo "make up              — Levanta los 4 servicios en modo desarrollo"
	@echo "make up-build        — Reconstruye imágenes y levanta servicios"
	@echo "make down            — Detiene y elimina contenedores"
	@echo "make logs            — Muestra logs de todos los servicios"
	@echo "make logs-backend    — Logs del backend (FastAPI)"
	@echo "make logs-db         — Logs de PostgreSQL"
	@echo "make logs-frontend   — Logs del frontend (Vite dev server)"
	@echo "make logs-nginx      — Logs de nginx"
	@echo "make shell-backend   — Abre shell interactiva en el contenedor backend"
	@echo "make shell-db        — Abre psql en el contenedor de base de datos"
	@echo "make migrate         — Corre alembic upgrade head"
	@echo "make migrate-status  — Muestra el estado actual de las migraciones"
	@echo "make migrate-history — Muestra el historial completo de migraciones"
	@echo "make migrate-down    — Revierte la última migración (-1)"
	@echo "make seed            — Carga datos iniciales de prueba en la base de datos"
	@echo "make test-backend    — Corre los tests del backend"
	@echo "make test-frontend   — Corre los tests del frontend"
	@echo "make clean           — Elimina contenedores, volúmenes e imágenes huérfanas"

up: ## Levanta los 4 servicios en modo desarrollo
	docker compose up -d
	@echo "Servicios iniciados:"
	@echo "  App:      http://localhost"
	@echo "  API:      http://localhost/api"
	@echo "  API Docs: http://localhost/docs"
	@echo "  pgAdmin:  http://localhost:5050"

up-build: ## Reconstruye imágenes y levanta servicios
	docker compose up -d --build
	@echo "Imágenes reconstruidas y servicios iniciados."

down: ## Detiene y elimina contenedores
	docker compose down
	@echo "Todos los contenedores detenidos."

logs: ## Muestra logs de todos los servicios
	docker compose logs -f

logs-backend: ## Logs del backend
	docker compose logs -f backend

logs-db: ## Logs de PostgreSQL
	docker compose logs -f db

logs-frontend: ## Logs del frontend
	docker compose logs -f frontend

logs-nginx: ## Logs de nginx
	docker compose logs -f nginx

shell-backend: ## Abre shell en el contenedor backend
	docker compose exec backend bash

shell-db: ## Abre psql en el contenedor de base de datos
	docker compose exec db sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

migrate: ## Corre alembic upgrade head dentro del contenedor backend
	docker compose exec backend sh -c 'cd /app/backend && alembic -c alembic.ini upgrade head'

migrate-status: ## Muestra el estado actual de las migraciones
	docker compose exec backend sh -c 'cd /app/backend && alembic -c alembic.ini current'

migrate-history: ## Muestra el historial completo de migraciones
	docker compose exec backend sh -c 'cd /app/backend && alembic -c alembic.ini history'

migrate-down: ## Revierte la última migración aplicada (-1)
	docker compose exec backend sh -c 'cd /app/backend && alembic -c alembic.ini downgrade -1'

seed: ## Carga datos iniciales de prueba en la base de datos
	docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"' < backend/database/seed.sql

test-backend: ## Corre los tests del backend
	docker compose exec backend pytest /app/backend/tests -v --cov=/app/backend/app --cov-report=term

test-frontend: ## Corre los tests del frontend
	docker compose exec frontend npm run test:run

clean: ## Elimina contenedores, volúmenes e imágenes huérfanas
	docker compose down -v --remove-orphans
	@echo "Volúmenes, contenedores e imágenes huérfanas eliminados."
