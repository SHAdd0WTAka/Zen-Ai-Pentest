# Zen Shield Sanitizer Service
# FastAPI microservice for data sanitization

FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 zen && chown -R zen:zen /app
USER zen

# Expose port
EXPOSE 9000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:9000/health')" || exit 1

# Run server
CMD ["python", "-m", "uvicorn", "zen_shield.server:app", "--host", "0.0.0.0", "--port", "9000"]
