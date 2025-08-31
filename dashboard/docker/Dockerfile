# Multi-stage build for production-ready dashboard
FROM node:18-alpine as frontend-build

# Set working directory for frontend
WORKDIR /app/frontend

# Copy frontend package files
COPY dashboard/frontend/package*.json ./

# Install frontend dependencies
RUN npm ci --only=production

# Copy frontend source
COPY dashboard/frontend/src ./src/
COPY dashboard/frontend/public ./public/

# Build frontend
RUN npm run build

# Python backend stage
FROM python:3.11-slim as backend

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend from previous stage
COPY --from=frontend-build /app/frontend/build ./dashboard/frontend/build/

# Create necessary directories
RUN mkdir -p logs data backups

# Set proper permissions
RUN chmod +x *.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/health || exit 1

# Expose port
EXPOSE ${PORT:-5000}

# Start command
CMD ["python", "dashboard/backend/dashboard_server.py"]