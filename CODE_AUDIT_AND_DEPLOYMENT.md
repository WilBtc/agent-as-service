# Code Audit & Deployment Automation Analysis

**Date**: 2025-10-25
**Platform**: Agent as a Service (AaaS) v2.0.0
**Audit Scope**: Code quality, deployment automation, intelligent orchestration

---

## Executive Summary

### Overall Assessment: **7/10**

The AaaS platform has a **solid foundation** with professional code quality, security features, and containerization. However, it **lacks critical automation** and intelligence features needed for production-scale deployment.

### Key Strengths ✅
- Clean, well-structured codebase
- Comprehensive test suite (100+ tests)
- Docker containerization ready
- API authentication and rate limiting
- Async architecture for performance
- Health check monitoring
- 8 specialized agent types

### Critical Gaps ❌
- **No CI/CD pipeline** - Manual deployment only
- **No auto-scaling** - Fixed capacity limits
- **No monitoring/metrics** - No observability
- **No automated recovery** - Manual intervention required
- **No Kubernetes support** - Not cloud-native ready
- **No load balancing** - Single point of failure
- **No deployment automation** - No scripts or workflows

---

## Detailed Audit Findings

## 1. Agent Deployment System

### Current Implementation

**File**: `src/aaas/agent_manager.py`

**Architecture**:
```python
AgentManager (Singleton)
    ├── ClaudeAgent instances (Dictionary)
    │   ├── ClaudeSDKClient (subprocess)
    │   ├── Working directory
    │   ├── Configuration
    │   └── Status tracking
    └── Resource management (Lock-based)
```

**Strengths**:
- ✅ Async/await pattern for non-blocking operations
- ✅ Lock-based concurrency control
- ✅ Proper resource cleanup on shutdown
- ✅ Context manager pattern for SDK client
- ✅ Conversation history tracking
- ✅ Automatic working directory creation

**Weaknesses**:
- ❌ **No health monitoring** - Agents can crash silently
- ❌ **No restart policy** - Failed agents stay failed
- ❌ **No resource limits** - Can consume unlimited memory/CPU
- ❌ **No idle timeout** - Agents run indefinitely
- ❌ **No graceful degradation** - Hard failures only
- ❌ **No agent pooling** - Each request creates new agent
- ❌ **No load balancing** - No distribution strategy

### Agent Lifecycle

**Current Flow**:
```
Create → Start → Running → Stop → Delete
              ↓
            Error (Terminal state)
```

**Missing States**:
- `IDLE` - Agent running but not processing
- `WARMING` - Agent preparing for work
- `RECOVERING` - Agent attempting recovery
- `DRAINING` - Agent finishing work before shutdown

**Recommendations**:

1. **Implement Health Monitoring**
```python
async def health_check_loop(self):
    """Periodically check agent health"""
    while self.status == AgentStatus.RUNNING:
        try:
            # Ping agent
            response = await self.client.ping()
            if not response:
                await self.restart()
        except Exception:
            self.status = AgentStatus.UNHEALTHY
            await self.recover()
        await asyncio.sleep(30)  # Check every 30s
```

2. **Add Auto-Recovery**
```python
async def recover(self):
    """Attempt to recover failed agent"""
    self.status = AgentStatus.RECOVERING
    max_retries = 3

    for attempt in range(max_retries):
        try:
            await self.stop()
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            await self.start()
            self.status = AgentStatus.RUNNING
            return True
        except Exception as e:
            logger.warning(f"Recovery attempt {attempt + 1} failed: {e}")

    self.status = AgentStatus.ERROR
    return False
```

3. **Implement Idle Timeout**
```python
async def idle_timeout_monitor(self):
    """Shutdown idle agents to save resources"""
    idle_timeout = settings.agent_idle_timeout  # e.g., 300 seconds

    while self.status == AgentStatus.RUNNING:
        if (datetime.utcnow() - self.last_activity).seconds > idle_timeout:
            logger.info(f"Agent {self.agent_id} idle timeout, shutting down")
            await self.stop()
            self.status = AgentStatus.IDLE
        await asyncio.sleep(60)
```

---

## 2. Configuration & Settings

### Current Implementation

**File**: `src/aaas/config.py`

**Current Settings**:
```python
max_agents: int = 100              # Static limit
agent_timeout: int = 3600          # 1 hour
rate_limit_per_minute: int = 60    # Fixed rate
```

**Strengths**:
- ✅ Environment variable support
- ✅ Pydantic validation
- ✅ Sensible defaults
- ✅ Security settings (API keys, CORS)

**Weaknesses**:
- ❌ **No dynamic configuration** - Requires restart
- ❌ **No environment detection** - Same settings for dev/prod
- ❌ **No auto-tuning** - Manual performance optimization
- ❌ **No monitoring thresholds** - No alerting triggers
- ❌ **No resource limits** - CPU/memory unconstrained

**Recommendations**:

1. **Add Smart Configuration**
```python
class Settings(BaseSettings):
    # Environment detection
    environment: str = "production"  # dev, staging, production

    # Auto-scaling
    min_agents: int = 1
    max_agents: int = 100
    scale_up_threshold: float = 0.8    # Scale at 80% capacity
    scale_down_threshold: float = 0.3  # Scale down at 30%

    # Resource limits
    max_memory_per_agent_mb: int = 512
    max_cpu_per_agent_percent: float = 25.0

    # Monitoring
    metrics_enabled: bool = True
    metrics_port: int = 9090
    alert_webhook_url: Optional[str] = None

    # Auto-recovery
    enable_auto_recovery: bool = True
    max_recovery_attempts: int = 3
    recovery_backoff_seconds: int = 5

    # Idle management
    agent_idle_timeout: int = 300  # 5 minutes
    enable_idle_shutdown: bool = True
```

2. **Environment-Specific Configs**
```python
def get_environment_config(env: str) -> dict:
    """Get environment-specific configuration"""
    configs = {
        "development": {
            "max_agents": 10,
            "log_level": "DEBUG",
            "rate_limit_enabled": False,
        },
        "staging": {
            "max_agents": 50,
            "log_level": "INFO",
            "rate_limit_enabled": True,
        },
        "production": {
            "max_agents": 100,
            "log_level": "WARNING",
            "rate_limit_enabled": True,
            "require_api_key": True,
        }
    }
    return configs.get(env, configs["production"])
```

---

## 3. Docker & Container Deployment

### Current Implementation

**File**: `Dockerfile`

**Strengths**:
- ✅ Multi-stage potential (slim base image)
- ✅ Non-root user (security best practice)
- ✅ Health check configured
- ✅ Proper layer caching
- ✅ Clean dependency management

**Weaknesses**:
- ❌ **No multi-stage build** - Larger image size
- ❌ **No layer optimization** - Could be smaller
- ❌ **Claude Code installation unclear** - Commented out
- ❌ **No build args** - Not configurable
- ❌ **No labels** - No metadata

**File**: `docker-compose.yml`

**Strengths**:
- ✅ Health check configured
- ✅ Restart policy
- ✅ Volume persistence
- ✅ Network isolation

**Weaknesses**:
- ❌ **Single service only** - No scaling
- ❌ **No database** - Stateless agents only
- ❌ **No reverse proxy** - No SSL termination
- ❌ **No monitoring** - No Prometheus/Grafana
- ❌ **No log aggregation** - No ELK stack

**Recommendations**:

1. **Optimized Multi-Stage Dockerfile**
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder
WORKDIR /build
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY src/ ./src/

# Labels for metadata
LABEL maintainer="WilBtc <telegram:@wilbtc>" \
      version="2.0.0" \
      description="Agent as a Service Platform"

# Non-root user
RUN useradd -m -u 1000 aaas && chown -R aaas:aaas /app
USER aaas

# Health check with better config
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["uvicorn", "aaas.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Production Docker Compose with Monitoring**
```yaml
version: '3.8'

services:
  aaas:
    build: .
    container_name: aaas-server
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ENVIRONMENT=production
      - METRICS_ENABLED=true
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
    networks:
      - aaas-network

  postgres:
    image: postgres:15-alpine
    container_name: aaas-db
    environment:
      - POSTGRES_DB=aaas
      - POSTGRES_USER=aaas
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - aaas-network

  redis:
    image: redis:7-alpine
    container_name: aaas-cache
    volumes:
      - redis-data:/data
    networks:
      - aaas-network

  prometheus:
    image: prom/prometheus:latest
    container_name: aaas-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - aaas-network

  grafana:
    image: grafana/grafana:latest
    container_name: aaas-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    networks:
      - aaas-network

  nginx:
    image: nginx:alpine
    container_name: aaas-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - aaas
    networks:
      - aaas-network

volumes:
  postgres-data:
  redis-data:
  prometheus-data:
  grafana-data:

networks:
  aaas-network:
    driver: bridge
```

---

## 4. CI/CD Pipeline

### Current State: **MISSING** ❌

No GitHub Actions, GitLab CI, or Jenkins pipelines found.

**Impact**:
- Manual testing required
- No automated builds
- Manual deployments
- No quality gates
- Slow release cycles

**Recommendation**: Implement comprehensive CI/CD

Create `.github/workflows/ci-cd.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    name: Test Suite
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        run: pytest --cov=src/aaas --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  lint:
    name: Code Quality
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install linters
        run: pip install ruff black mypy

      - name: Run ruff
        run: ruff check src/

      - name: Run black
        run: black --check src/

      - name: Run mypy
        run: mypy src/

  security:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json

      - name: Run Safety
        run: |
          pip install safety
          safety check --json

      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: bandit-report.json

  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [test, lint, security]
    if: github.event_name == 'push'

    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=sha
            type=semver,pattern={{version}}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: staging

    steps:
      - name: Deploy to staging server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            cd /opt/aaas
            docker-compose pull
            docker-compose up -d
            docker-compose ps

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
      - name: Deploy to production
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/aaas
            docker-compose pull
            docker-compose up -d --no-deps aaas

      - name: Health check
        run: |
          sleep 10
          curl -f https://api.aaas.example.com/health || exit 1

      - name: Notify deployment
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Production deployment completed'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 5. Kubernetes Deployment

### Current State: **MISSING** ❌

No Kubernetes manifests or Helm charts found.

**Impact**:
- Cannot deploy to cloud platforms (GKE, EKS, AKS)
- No horizontal pod autoscaling
- No rolling updates
- No service mesh capabilities
- Limited scalability

**Recommendation**: Create Kubernetes manifests

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aaas-deployment
  labels:
    app: aaas
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
        image: ghcr.io/wilbtc/agent-as-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: aaas-secrets
              key: anthropic-api-key
        - name: ENVIRONMENT
          value: "production"
        - name: MAX_AGENTS
          value: "50"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
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
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aaas-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aaas-deployment
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 6. Monitoring & Observability

### Current State: **BASIC** ⚠️

**Current Capabilities**:
- ✅ Health check endpoint (`/health`)
- ✅ Basic logging (console output)
- ✅ Agent count tracking

**Missing**:
- ❌ **Metrics collection** - No Prometheus integration
- ❌ **Distributed tracing** - No request tracking
- ❌ **Alerting** - No automated alerts
- ❌ **Dashboards** - No visualization
- ❌ **Log aggregation** - No centralized logging
- ❌ **Performance metrics** - No latency tracking
- ❌ **Error tracking** - No Sentry integration

**Recommendation**: Implement comprehensive monitoring

1. **Add Prometheus Metrics**

Create `src/aaas/metrics.py`:

```python
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from fastapi import Response

# Metrics
agent_create_counter = Counter(
    'aaas_agents_created_total',
    'Total number of agents created',
    ['agent_type']
)

agent_delete_counter = Counter(
    'aaas_agents_deleted_total',
    'Total number of agents deleted'
)

agent_error_counter = Counter(
    'aaas_agent_errors_total',
    'Total number of agent errors',
    ['error_type']
)

active_agents_gauge = Gauge(
    'aaas_active_agents',
    'Number of currently active agents',
    ['status']
)

message_duration_histogram = Histogram(
    'aaas_message_duration_seconds',
    'Time spent processing messages',
    ['agent_type']
)

request_duration_histogram = Histogram(
    'aaas_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

2. **Add Structured Logging**

```python
import structlog
from pythonjsonlogger import jsonlogger

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage
logger.info(
    "agent_created",
    agent_id=agent_id,
    agent_type=config.agent_type,
    user_id=user_id
)
```

3. **Add Distributed Tracing**

```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Usage
tracer = trace.get_tracer(__name__)

async def create_agent(config):
    with tracer.start_as_current_span("create_agent") as span:
        span.set_attribute("agent.type", config.agent_type)
        # ... agent creation logic
```

---

## 7. Auto-Scaling Implementation

### Current State: **NONE** ❌

The system has fixed limits with no automatic scaling.

**Recommendation**: Implement intelligent auto-scaling

Create `src/aaas/autoscaler.py`:

```python
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class AgentAutoscaler:
    """Intelligent agent auto-scaling based on demand"""

    def __init__(self, manager, settings):
        self.manager = manager
        self.settings = settings
        self.metrics_window = timedelta(minutes=5)
        self.request_history = []
        self._running = False

    async def start(self):
        """Start autoscaling loop"""
        self._running = True
        logger.info("Starting autoscaler")

        while self._running:
            try:
                await self._autoscale_check()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Autoscaling error: {e}", exc_info=True)

    async def stop(self):
        """Stop autoscaling"""
        self._running = False
        logger.info("Stopping autoscaler")

    async def _autoscale_check(self):
        """Check if scaling is needed"""
        agents = await self.manager.list_agents()
        current_count = len(agents)

        # Calculate demand metrics
        recent_requests = self._get_recent_request_rate()
        utilization = current_count / self.settings.max_agents

        # Scale up decision
        if (utilization > self.settings.scale_up_threshold and
            current_count < self.settings.max_agents and
            recent_requests > current_count * 0.8):

            scale_up_count = min(
                int(current_count * 0.5),  # Scale by 50%
                self.settings.max_agents - current_count
            )
            await self._scale_up(scale_up_count)

        # Scale down decision
        elif (utilization < self.settings.scale_down_threshold and
              current_count > self.settings.min_agents and
              recent_requests < current_count * 0.3):

            scale_down_count = int(current_count * 0.3)  # Reduce by 30%
            await self._scale_down(scale_down_count)

    async def _scale_up(self, count: int):
        """Scale up by creating idle agents"""
        logger.info(f"Scaling up: creating {count} idle agents")

        for _ in range(count):
            try:
                config = AgentConfig(agent_type=AgentType.GENERAL)
                agent_id = await self.manager.create_agent(config, auto_start=False)
                logger.info(f"Created idle agent {agent_id}")
            except Exception as e:
                logger.error(f"Failed to create agent: {e}")

    async def _scale_down(self, count: int):
        """Scale down by removing idle agents"""
        logger.info(f"Scaling down: removing {count} idle agents")

        agents = await self.manager.list_agents()
        idle_agents = [
            (id, agent) for id, agent in agents.items()
            if agent.status == AgentStatus.IDLE or
            (agent.status == AgentStatus.RUNNING and agent.messages_count == 0)
        ]

        # Remove oldest idle agents
        idle_agents.sort(key=lambda x: x[1].created_at)
        for agent_id, _ in idle_agents[:count]:
            try:
                await self.manager.delete_agent(agent_id)
                logger.info(f"Removed idle agent {agent_id}")
            except Exception as e:
                logger.error(f"Failed to remove agent {agent_id}: {e}")

    def track_request(self):
        """Track a request for autoscaling decisions"""
        now = datetime.utcnow()
        self.request_history.append(now)

        # Clean old entries
        cutoff = now - self.metrics_window
        self.request_history = [
            ts for ts in self.request_history if ts > cutoff
        ]

    def _get_recent_request_rate(self) -> float:
        """Get request rate per minute"""
        if not self.request_history:
            return 0.0

        window_minutes = self.metrics_window.total_seconds() / 60
        return len(self.request_history) / window_minutes
```

---

## 8. Deployment Automation Scripts

### Current State: **NONE** ❌

No deployment scripts found.

**Recommendation**: Create deployment automation

Create `scripts/deploy.sh`:

```bash
#!/bin/bash
set -e

# AaaS Deployment Script
# Usage: ./scripts/deploy.sh [environment]

ENVIRONMENT=${1:-production}
VERSION=${2:-latest}

echo "🚀 Deploying AaaS to ${ENVIRONMENT}..."

# Load environment-specific config
case $ENVIRONMENT in
    "production")
        ENV_FILE=".env.production"
        COMPOSE_FILE="docker-compose.prod.yml"
        ;;
    "staging")
        ENV_FILE=".env.staging"
        COMPOSE_FILE="docker-compose.staging.yml"
        ;;
    "development")
        ENV_FILE=".env.development"
        COMPOSE_FILE="docker-compose.yml"
        ;;
    *)
        echo "❌ Unknown environment: ${ENVIRONMENT}"
        exit 1
        ;;
esac

# Pre-deployment checks
echo "✅ Running pre-deployment checks..."

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Environment file not found: ${ENV_FILE}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi

# Check if API key is set
if ! grep -q "ANTHROPIC_API_KEY" "$ENV_FILE"; then
    echo "❌ ANTHROPIC_API_KEY not set in ${ENV_FILE}"
    exit 1
fi

# Pull latest code (if in git repo)
if [ -d ".git" ]; then
    echo "📥 Pulling latest code..."
    git pull origin main
fi

# Run tests
echo "🧪 Running tests..."
pytest tests/ --maxfail=5 || {
    echo "❌ Tests failed, aborting deployment"
    exit 1
}

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t aaas:${VERSION} .

# Backup current deployment
if docker ps | grep -q aaas-server; then
    echo "💾 Backing up current deployment..."
    docker commit aaas-server aaas:backup-$(date +%Y%m%d-%H%M%S)
fi

# Deploy with zero downtime
echo "🚀 Deploying new version..."

# Start new container
docker-compose -f ${COMPOSE_FILE} --env-file ${ENV_FILE} up -d --no-deps --build aaas

# Wait for health check
echo "⏳ Waiting for health check..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Health check passed!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Health check failed after 30 attempts"
        echo "🔄 Rolling back..."
        docker-compose -f ${COMPOSE_FILE} down
        docker run -d --name aaas-server aaas:backup-latest
        exit 1
    fi
    sleep 2
done

# Cleanup old images
echo "🧹 Cleaning up old images..."
docker image prune -f --filter "until=24h"

# Print deployment info
echo ""
echo "✅ Deployment successful!"
echo "🌐 Service URL: http://localhost:8000"
echo "📊 Health: http://localhost:8000/health"
echo "📚 Docs: http://localhost:8000/docs"
echo ""
echo "📝 Logs: docker-compose -f ${COMPOSE_FILE} logs -f aaas"
```

---

## Summary of Recommendations

### Priority 1: Critical (Immediate Action Required)

1. **Implement CI/CD Pipeline**
   - GitHub Actions for automated testing and deployment
   - Automated security scanning
   - Docker image building and publishing

2. **Add Health Monitoring & Auto-Recovery**
   - Periodic health checks for agents
   - Automatic restart on failure
   - Graceful degradation

3. **Implement Metrics & Observability**
   - Prometheus metrics
   - Structured logging
   - Distributed tracing

### Priority 2: Important (Within 2 Weeks)

4. **Add Auto-Scaling**
   - Demand-based agent scaling
   - Resource-aware scaling
   - Idle agent cleanup

5. **Create Kubernetes Manifests**
   - Deployment configurations
   - Horizontal Pod Autoscaler
   - Service mesh integration

6. **Deployment Automation**
   - Deployment scripts
   - Rollback procedures
   - Environment management

### Priority 3: Enhanced Features (Within 1 Month)

7. **Advanced Monitoring**
   - Grafana dashboards
   - Alert management
   - Performance analytics

8. **Database Integration**
   - PostgreSQL for persistence
   - Redis for caching
   - Agent state persistence

9. **Load Balancing & HA**
   - Nginx reverse proxy
   - SSL termination
   - Multi-region deployment

---

## Estimated Implementation Timeline

| Feature | Effort | Timeline |
|---------|--------|----------|
| CI/CD Pipeline | 2-3 days | Week 1 |
| Health Monitoring | 1-2 days | Week 1 |
| Metrics & Logging | 2-3 days | Week 1 |
| Auto-scaling | 3-4 days | Week 2 |
| Kubernetes Setup | 2-3 days | Week 2 |
| Deployment Scripts | 1-2 days | Week 2 |
| Advanced Monitoring | 3-4 days | Week 3 |
| Database Integration | 4-5 days | Week 3-4 |
| Load Balancing | 2-3 days | Week 4 |

**Total**: ~3-4 weeks for full implementation

---

## Conclusion

The AaaS codebase is **professionally structured** with good security practices and testing. However, it **lacks critical production automation** features needed for real-world deployment at scale.

**Current Readiness**: 7/10
**After Improvements**: 10/10

Implementing the recommended automation features will transform AaaS from a **well-built prototype** into a **production-ready, enterprise-grade platform** capable of:

- ✅ Automatic deployment and scaling
- ✅ Self-healing and recovery
- ✅ Comprehensive monitoring and alerting
- ✅ Zero-downtime updates
- ✅ Cloud-native deployment
- ✅ High availability and fault tolerance

---

**Next Steps**: Prioritize implementing CI/CD pipeline and health monitoring as these provide the highest immediate value.
