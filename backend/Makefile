.PHONY: help setup up down restart logs db-shell db-reset clean status

help:
	@echo "FashionVision AI - Backend Commands"
	@echo "==========================="
	@echo "make setup         - Create .env from .env.example (first time)"
	@echo "make up           - Start all services (DB + Backend)"
	@echo "make down         - Stop all services"
	@echo "make restart     - Restart services"
	@echo "make logs       - View logs"
	@echo "make db-shell   - Open PostgreSQL shell"
	@echo "make db-reset   - Reset database (WARNING: deletes data)"
	@echo "make clean     - Remove images and volumes"
	@echo "make status    - Show container status"

setup:
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env file"; else echo ".env already exists"; fi

up:
	docker-compose up -d
	@echo "Services started: http://localhost:8000 (API), http://localhost:5432 (PostgreSQL)"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-db:
	docker-compose logs -f db

db-shell:
	docker-compose exec db psql -U fashionvision_ai_user -d fashionvision_ai

db-reset:
	docker-compose down -v
	docker-compose up -d
	@echo "Database reset complete"

clean:
	docker-compose down -v --remove-orphans
	@echo "All volumes and containers removed"

status:
	docker-compose ps