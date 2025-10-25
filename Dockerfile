# ========================================
# Stage 1: Builder - Install dependencies
# ========================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (better layer caching)
COPY requirements.txt pyproject.toml ./

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Install the application
RUN pip install --no-cache-dir -e .


# ========================================
# Stage 2: Runtime - Minimal final image
# ========================================
FROM python:3.11-slim

# Set metadata
LABEL maintainer="WilBtc <noreply@example.com>"
LABEL version="2.0.0"
LABEL description="Agent as a Service - Enterprise AI Agent Platform"

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY --from=builder /build/src ./src
COPY pyproject.toml ./

# Set PATH to use venv
ENV PATH="/opt/venv/bin:$PATH"

# Create necessary directories with correct permissions
RUN mkdir -p /app/data /app/logs /tmp/aaas-agents && \
    chmod 755 /app/data /app/logs /tmp/aaas-agents

# Create non-root user with specific UID/GID for security
RUN groupadd -r -g 1000 aaas && \
    useradd -r -u 1000 -g aaas -m -s /bin/bash aaas && \
    chown -R aaas:aaas /app /tmp/aaas-agents

# Switch to non-root user
USER aaas

# Expose application port
EXPOSE 8000

# Expose metrics port
EXPOSE 9090

# Health check with proper timing
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    # Python optimizations
    PYTHONHASHSEED=random \
    # Pip configuration
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Application defaults
    ENVIRONMENT=production \
    LOG_LEVEL=INFO

# Add health check script
COPY --chown=aaas:aaas <<'EOF' /app/healthcheck.sh
#!/bin/bash
# Enhanced health check script
response=$(curl -sf http://localhost:8000/health)
if [ $? -ne 0 ]; then
    exit 1
fi

status=$(echo $response | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$status" != "healthy" ]; then
    exit 1
fi

exit 0
EOF

RUN chmod +x /app/healthcheck.sh

# Run the application
CMD ["python", "-m", "uvicorn", "aaas.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-level", "info"]
