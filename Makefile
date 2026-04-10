# === Python Backend ===

# Virtual environment path
ENV ?= .venv
PYTHON = $(ENV)/bin/python
UV = uv

# Create Python virtual environment using uv
.PHONY: venv
venv:
	$(UV) venv $(ENV)

# Install backend dependencies
.PHONY: install
install: venv
	$(UV) pip install -r requirements.txt

# Format backend code with Black
.PHONY: format
format:
	$(PYTHON) -m black langchain_ai_agent

# Lint backend with Flake8
.PHONY: lint
lint:
	$(PYTHON) -m flake8 langchain_ai_agent --exclude=.venv,.git,__pycache__,.mypy_cache

# Run backend unit tests with pytest
.PHONY: test
test:
	$(PYTHON) -m pytest -v tests/

# Run FastAPI API server only (no pipeline)
.PHONY: api
api:
	$(PYTHON) -m uvicorn langchain_ai_agent.api.main:app --reload --host 0.0.0.0 --port 8000

# Clean Python artifacts
.PHONY: clean
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache
	find . -name '*.pyc' -delete

# === Frontend (Next.js UI) ===

FRONTEND_DIR = frontend

# Install frontend dependencies
.PHONY: ui-install
ui-install:
	cd $(FRONTEND_DIR) && npm install

# Run frontend dev server
.PHONY: ui
ui:
	cd $(FRONTEND_DIR) && npm run dev

# Build frontend for production
.PHONY: ui-build
ui-build:
	cd $(FRONTEND_DIR) && npm run build

# Clean frontend artifacts
.PHONY: ui-clean
ui-clean:
	cd $(FRONTEND_DIR) && rm -rf .next node_modules

# === Docker ===

IMAGE_NAME = langchain-agent

# Build Docker image (backend + frontend)
.PHONY: docker-build
docker-build:
	docker build -t $(IMAGE_NAME) .

# Run Docker container exposing backend
.PHONY: docker-run
docker-run:
	docker run -p 8000:8000 $(IMAGE_NAME)

# Rebuild Docker image with no cache
.PHONY: docker-rebuild
docker-rebuild:
	docker build --no-cache -t $(IMAGE_NAME) .

# Remove Docker image
.PHONY: docker-clean
docker-clean:
	docker rmi -f $(IMAGE_NAME)

# === Combined Dev Workflow ===

# Launch both backend (FastAPI) and frontend (Next.js)
.PHONY: run
run:
	@echo "🚀 Launching backend at http://localhost:8000 and frontend at http://localhost:3000"
	@$(MAKE) -j2 api ui

# === All-in-One ===

# Full backend check: install, lint, test
.PHONY: all
all: install lint test
