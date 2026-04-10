# --------------------------
# 🐍 Backend Build Stage
# --------------------------
FROM python:3.10-slim-bookworm AS backend

# Set working directory
WORKDIR /app

# Copy backend code and configs
COPY ./langchain_ai_agent ./langchain_ai_agent
COPY requirements.txt .
COPY pyproject.toml .

# Install backend dependencies using uv
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv && \
    uv pip install -r requirements.txt

# --------------------------
# 🎨 Frontend Build Stage
# --------------------------
FROM node:20 AS frontend

# Set working directory for frontend
WORKDIR /frontend

# Copy frontend code and build it
COPY frontend/ .
RUN npm install && npm run build

# --------------------------
# 🚀 Final Runtime Stage
# --------------------------
FROM python:3.10-slim-bookworm

# Set workdir and copy built backend
WORKDIR /app
COPY --from=backend /app /app

# Copy frontend static build output
COPY --from=frontend /frontend/out /app/frontend_build

# Install minimal runtime deps
RUN pip install --no-cache-dir uvicorn[standard] fastapi

# Expose the FastAPI port
EXPOSE 8000

# Run the API server
CMD ["uvicorn", "langchain_ai_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
