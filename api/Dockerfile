FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application
COPY kimi_personas_api.py .
COPY README.md .

# Create personas directory
RUN mkdir -p /root/.config/kimi/personas

# Copy personas (will be overridden by volume mount)
COPY personas/ /root/.config/kimi/personas/ 2>/dev/null || true

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:5000/api/v1/health')" || exit 1

# Run
CMD ["python3", "kimi_personas_api.py", "-H", "0.0.0.0", "-p", "5000"]
