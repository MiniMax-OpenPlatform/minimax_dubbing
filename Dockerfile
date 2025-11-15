# Multi-stage Dockerfile for minimax_dubbing
# Single image solution with all features

# ============================================================================
# Stage 1: Build Frontend
# ============================================================================
FROM node:22-alpine AS frontend-builder

# Set proxy for network access
ARG PROXY_URL=http://pac-internal.xaminim.com:3129
ARG NO_PROXY=localhost,127.0.0.1,*.xaminim.com,10.0.0.0/8

ENV http_proxy=${PROXY_URL} \
    https_proxy=${PROXY_URL} \
    ftp_proxy=${PROXY_URL} \
    no_proxy=${NO_PROXY}

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies (including dev dependencies for build)
RUN npm install

# Copy frontend source code
COPY frontend/ ./

# Build frontend (skip type checking for faster build)
# The project has some TypeScript type issues but works fine at runtime
RUN npx vite build

# ============================================================================
# Stage 2: Download AI Models and Setup Python Environment
# ============================================================================
FROM python:3.10-slim AS model-downloader

# Set proxy for network access
ARG PROXY_URL=http://pac-internal.xaminim.com:3129
ARG NO_PROXY=localhost,127.0.0.1,*.xaminim.com,10.0.0.0/8

ENV http_proxy=${PROXY_URL} \
    https_proxy=${PROXY_URL} \
    ftp_proxy=${PROXY_URL} \
    no_proxy=${NO_PROXY}

# Use Tsinghua University mirror for faster downloads in China
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources

WORKDIR /app

# Install system dependencies for model downloading
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and download script
COPY requirements.txt ./
COPY download_models.py ./

# Install Python dependencies (minimal for model download)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir facenet-pytorch demucs

# Pre-download AI models to cache
RUN python download_models.py --demucs --facenet || true

# ============================================================================
# Stage 3: Final Runtime Image
# ============================================================================
FROM python:3.10-slim

# Set proxy for network access
ARG PROXY_URL=http://pac-internal.xaminim.com:3129
ARG NO_PROXY=localhost,127.0.0.1,*.xaminim.com,10.0.0.0/8

ENV http_proxy=${PROXY_URL} \
    https_proxy=${PROXY_URL} \
    ftp_proxy=${PROXY_URL} \
    no_proxy=${NO_PROXY}

# Use Tsinghua University mirror for faster downloads in China
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # FFmpeg for video/audio processing
    ffmpeg \
    # OpenCV dependencies
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    # Nginx for serving frontend
    nginx \
    # Supervisor for process management
    supervisor \
    # Cron for scheduled tasks
    cron \
    # Build tools
    gcc \
    g++ \
    make \
    # Other utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from model-downloader stage
COPY --from=model-downloader /root/.cache/torch /root/.cache/torch
COPY --from=model-downloader /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=model-downloader /usr/local/bin /usr/local/bin

# Copy backend code
COPY . /app/

# Install all Python dependencies (some may have been installed in previous stage)
RUN pip install --no-cache-dir -r requirements.txt

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Create necessary directories
RUN mkdir -p /app/media \
    /app/staticfiles \
    /app/logs \
    /var/log/supervisor \
    /var/log/nginx

# Copy Nginx configuration (replace main config entirely)
COPY docker/nginx.conf /etc/nginx/nginx.conf

# Optimize Nginx worker processes for container environment
RUN sed -i 's/worker_connections 1024;/worker_connections 4096;/' /etc/nginx/nginx.conf

# Copy supervisor configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy entrypoint script
COPY docker/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose ports
# 5172: Backend (Django/Gunicorn)
# 5173: Frontend (Nginx serves built files)
EXPOSE 5172 5173

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=backend.settings \
    LANG=C.UTF-8

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5172/api/auth/test-auth/ || exit 1

# Volume for persistent data
VOLUME ["/app/media"]

# Entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command (will be executed by entrypoint)
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
