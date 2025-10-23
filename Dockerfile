FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
# Note: Adjust this based on actual Claude Code installation method
RUN pip install --no-cache-dir anthropic-claude-code || \
    echo "Claude Code installation - adjust based on official method"

# Copy application files
COPY requirements.txt pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /tmp/aaas-agents

# Create non-root user
RUN useradd -m -u 1000 aaas && \
    chown -R aaas:aaas /app /tmp/aaas-agents

# Switch to non-root user
USER aaas

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000

# Run the server
CMD ["aaas", "serve", "--host", "0.0.0.0", "--port", "8000"]
