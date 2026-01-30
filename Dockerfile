# =============================================================================
# Zen AI Pentest - Multi-Stage Dockerfile
# =============================================================================
# Supports three build targets:
#   - development: Full dev environment with all tools
#   - production: Optimized production image
#   - worker: Lightweight worker node
#
# Build commands:
#   docker build --target production -t zen-ai-pentest:latest .
#   docker build --target development -t zen-ai-pentest:dev .
#   docker build --target worker -t zen-ai-pentest:worker -f Dockerfile.worker .
# =============================================================================

# =============================================================================
# STAGE 1: Base Image
# =============================================================================
FROM python:3.14-slim-bookworm AS base

LABEL maintainer="SHAdd0WTAka + Kimi AI"
LABEL description="Zen AI Pentest Framework"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.0 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Set work directory
WORKDIR /app

# Install system dependencies (common for all stages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# STAGE 2: Development Image
# =============================================================================
FROM base AS development

# Install development and security tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    pkg-config \
    # Security tools
    nmap \
    masscan \
    nikto \
    sqlmap \
    gobuster \
    dirb \
    hydra \
    john \
    hashcat \
    ncrack \
    # Network tools
    netcat-traditional \
    socat \
    ncat \
    tcpdump \
    wireshark-common \
    tshark \
    dnsutils \
    whois \
    # Web tools
    curl \
    wget \
    httpie \
    # Utilities
    vim \
    nano \
    git \
    tmux \
    screen \
    htop \
    tree \
    jq \
    yq \
    # Python dev
    python3-dev \
    python3-pip \
    python3-venv \
    # Other
    libpcap-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Go (for Go-based tools)
ENV GOLANG_VERSION=1.21.5
RUN curl -fsSL "https://golang.org/dl/go${GOLANG_VERSION}.linux-amd64.tar.gz" | tar -C /usr/local -xz
ENV PATH=$PATH:/usr/local/go/bin:/root/go/bin

# Install additional Go tools
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest \
    && go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest \
    && go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest \
    && go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest \
    && go install -v github.com/projectdiscovery/katana/cmd/katana@latest \
    && go install -v github.com/OJ/gobuster/v3@latest

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (including dev)
RUN poetry install --with dev --no-root

# Copy application code
COPY . .

# Install the package in editable mode
RUN poetry install

# Create non-root user for security
RUN useradd -m -u 1000 pentest && \
    chown -R pentest:pentest /app
USER pentest

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import zen_ai_pentest; print('OK')" || exit 1

# Default command
CMD ["poetry", "run", "python", "-m", "zen_ai_pentest", "--help"]

# =============================================================================
# STAGE 3: Production Image
# =============================================================================
FROM base AS production

# Install only production dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Minimal security tools
    nmap \
    curl \
    dnsutils \
    whois \
    # Python runtime
    libpq5 \
    libssl3 \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r pentest && useradd -r -g pentest -u 1000 pentest

# Copy requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=pentest:pentest . .

# Create necessary directories
RUN mkdir -p /app/logs /app/evidence /app/reports /app/sessions /app/data && \
    chown -R pentest:pentest /app

# Switch to non-root user
USER pentest

# Expose ports
EXPOSE 8080 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "
import urllib.request
try:
    urllib.request.urlopen('http://localhost:8080/health')
    exit(0)
except:
    exit(1)
" || exit 1

# Set entrypoint
ENTRYPOINT ["python", "-m", "zen_ai_pentest"]

# Default command
CMD ["--help"]

# =============================================================================
# STAGE 4: Builder (for compiling dependencies)
# =============================================================================
FROM base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# STAGE 5: Final Minimal Image
# =============================================================================
FROM python:3.14-alpine AS minimal

# Install only runtime dependencies
RUN apk add --no-cache \
    libpq \
    libffi \
    openssl \
    ca-certificates

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN addgroup -g 1000 pentest && \
    adduser -D -u 1000 -G pentest pentest

# Copy application
COPY --chown=pentest:pentest . /app
WORKDIR /app

# Switch to non-root user
USER pentest

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import zen_ai_pentest" || exit 1

ENTRYPOINT ["python", "-m", "zen_ai_pentest"]
