# Zen AI Pentest - Production Docker Image
FROM python:3.11-slim

LABEL maintainer="SHAdd0WTAka" \
      version="2.0.0" \
      description="Autonomous Red Team Framework"

# Security: Run as non-root user
RUN groupadd -r zenai && useradd -r -g zenai zenai

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    nmap \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e "."

# Copy application code
COPY . .

# Install in editable mode
RUN pip install --no-cache-dir -e "."

# Create necessary directories
RUN mkdir -p logs evidence sessions data && \
    chown -R zenai:zenai /app

# Switch to non-root user
USER zenai

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "web_ui.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
