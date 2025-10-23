# Deployment Guide

Guide for deploying Agent as a Service (AaaS) in production environments.

## Production Deployment Options

### 1. Docker Deployment

#### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Claude Code
RUN pip install claude-code

# Copy application
COPY . .

# Install dependencies
RUN pip install -e .

# Create directories
RUN mkdir -p /app/data /app/logs /tmp/aaas-agents

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

# Run the server
CMD ["aaas", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  aaas:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - MAX_AGENTS=50
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 2. Kubernetes Deployment

#### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aaas-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aaas
  template:
    metadata:
      labels:
        app: aaas
    spec:
      containers:
      - name: aaas
        image: wilbtc/aaas:latest
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: aaas-secrets
              key: api-key
        - name: MAX_AGENTS
          value: "50"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: aaas-service
spec:
  selector:
    app: aaas
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. Systemd Service

For direct deployment on Linux servers:

```ini
[Unit]
Description=Agent as a Service
After=network.target

[Service]
Type=simple
User=aaas
WorkingDirectory=/opt/aaas
Environment="PATH=/opt/aaas/venv/bin"
EnvironmentFile=/opt/aaas/.env
ExecStart=/opt/aaas/venv/bin/aaas serve
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Production Configuration

### Environment Variables

```bash
# API Configuration
HOST=0.0.0.0
PORT=8000

# Claude Code
ANTHROPIC_API_KEY=your-production-key
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# Scaling
MAX_AGENTS=100
AGENT_TIMEOUT=3600

# Storage (use persistent volumes)
DATA_DIR=/var/lib/aaas/data
LOGS_DIR=/var/log/aaas
DEFAULT_WORKING_DIR=/var/lib/aaas/agents

# Security
API_KEY_HEADER=X-API-Key
ALLOWED_ORIGINS=https://yourdomain.com

# Logging
LOG_LEVEL=WARNING
LOG_FORMAT=json
```

## Security Considerations

### 1. API Authentication

Implement API key authentication:

```python
# Add to your API gateway or reverse proxy
headers = {
    "X-API-Key": "your-secure-api-key"
}
```

### 2. HTTPS/TLS

Use a reverse proxy (nginx, Caddy, or traefik) for TLS termination:

```nginx
server {
    listen 443 ssl http2;
    server_name aaas.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Network Security

- Use firewalls to restrict access
- Deploy in private VPC/network
- Use security groups/network policies
- Implement rate limiting

### 4. Secrets Management

Use secure secret storage:

```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id aaas/api-key

# Kubernetes Secrets
kubectl create secret generic aaas-secrets \
  --from-literal=api-key=your-key

# HashiCorp Vault
vault kv get secret/aaas/api-key
```

## Monitoring

### Health Checks

```bash
# Simple health check
curl http://localhost:8000/health

# Detailed monitoring
curl http://localhost:8000/api/v1/agents | jq
```

### Logging

Configure structured logging:

```python
# Custom logging configuration
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### Metrics

Integrate with monitoring tools:

- Prometheus for metrics
- Grafana for visualization
- ELK stack for log aggregation
- DataDog/New Relic for APM

## Scaling

### Horizontal Scaling

Deploy multiple AaaS instances behind a load balancer:

```yaml
# Increase replicas in Kubernetes
kubectl scale deployment aaas-deployment --replicas=5
```

### Vertical Scaling

Adjust resources per instance:

```yaml
resources:
  limits:
    memory: "4Gi"
    cpu: "4000m"
```

## Backup and Recovery

### Data Backup

```bash
# Backup data directory
tar -czf aaas-backup-$(date +%Y%m%d).tar.gz /var/lib/aaas/data

# Backup to S3
aws s3 sync /var/lib/aaas/data s3://your-bucket/aaas-backup/
```

### Disaster Recovery

1. Store backups in multiple locations
2. Test recovery procedures regularly
3. Document recovery steps
4. Implement automated backup schedules

## Performance Optimization

### 1. Process Pool

Configure worker processes:

```bash
gunicorn aaas.api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### 2. Caching

Implement caching for frequently accessed data:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_agent_template(template_name: str):
    # Cache template configurations
    pass
```

### 3. Database

For production, consider using a proper database:

- PostgreSQL for agent metadata
- Redis for session management
- MongoDB for agent logs

## Maintenance

### Updates

```bash
# Pull latest version
git pull origin main

# Update dependencies
pip install -e . --upgrade

# Restart service
systemctl restart aaas
```

### Database Migrations

```bash
# Run migrations (if using database)
alembic upgrade head
```

## Cost Optimization

1. **Auto-scaling**: Scale based on demand
2. **Spot instances**: Use for non-critical workloads
3. **Resource limits**: Set appropriate CPU/memory limits
4. **Monitoring**: Track and optimize API usage

## Support

For production deployment support:
- Telegram: [@wilbtc](https://t.me/wilbtc)
- Email: support@wilbtc.com
