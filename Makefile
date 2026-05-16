# Makefile for Execra project
# Centralises common commands for developers and contributors

# Variables
PYTHON = python
PIP = pip
UVICORN = uvicorn
PYTEST = pytest
DOCKER_COMPOSE = docker-compose

.DEFAULT_GOAL := help

.PHONY: help install dev test test-unit test-integration coverage lint format docs models health docker-up docker-down clean

# Default target: show help
help:
	@echo "Execra Management Commands:"
	@echo "  make install            Install dependencies"
	@echo "  make dev                Run the development server"
	@echo "  make test               Run all tests"
	@echo "  make test-unit          Run unit tests"
	@echo "  make test-integration   Run integration tests"
	@echo "  make coverage           Run tests and generate coverage report"
	@echo "  make lint               Run linting checks (flake8, mypy)"
	@echo "  make format             Format code (black, isort)"
	@echo "  make docs               Serve documentation"
	@echo "  make models             Download required models"
	@echo "  make health             Run system health check"
	@echo "  make docker-up          Start services with Docker Compose"
	@echo "  make docker-down        Stop Docker Compose services"
	@echo "  make clean              Remove temporary files and caches"

# Prerequisite: requirements.txt and requirements-dev.txt must exist
install:
	$(PIP) install -r requirements.txt -r requirements-dev.txt

# Prerequisite: api/main.py must exist
dev:
	$(UVICORN) api.main:app --reload --host 0.0.0.0 --port 8000

# Prerequisite: tests/ directory must exist
test:
	$(PYTHON) -m $(PYTEST) tests/ -v

# Prerequisite: tests/unit/ directory must exist
test-unit:
	$(PYTHON) -m $(PYTEST) tests/unit/ -v

# Prerequisite: tests/integration/ directory must exist
test-integration:
	$(PYTHON) -m $(PYTEST) tests/integration/ -v

# Prerequisite: core/ and api/ directories must exist
coverage:
	$(PYTHON) -m $(PYTEST) --cov=core --cov=api --cov-report=html

# Prerequisite: core/ and api/ directories must exist; flake8 and mypy installed
lint:
	flake8 core/ api/ && mypy core/ api/

# Prerequisite: core/, api/, and tests/ directories must exist; black and isort installed
format:
	black core/ api/ tests/ && isort core/ api/ tests/

# Prerequisite: mkdocs.yml must exist
docs:
	mkdocs serve

# Prerequisite: scripts/download_models.py must exist
models:
	$(PYTHON) scripts/download_models.py

# Prerequisite: scripts/health_check.py must exist
health:
	$(PYTHON) scripts/health_check.py

# Prerequisite: docker-compose.yml must exist
docker-up:
	$(DOCKER_COMPOSE) up --build -d

# Prerequisite: Docker Compose services must be running
docker-down:
	$(DOCKER_COMPOSE) down

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache htmlcov/ logs/
