# Agent as a Service - Deployment Guide

## Production Deployment Options

### Option 1: Kubernetes (Recommended for Scale)

#### Prerequisites
- Kubernetes cluster (1.24+)
- kubectl configured
- Docker registry access (GHCR)

#### Quick Start
```bash
# 1. Create secrets
kubectl create secret generic aaas-secrets \
  --from-literal=ANTHROPIC_API_KEY=your-key \
  --from-literal=API_KEY=your-api-key \
  -n aaas

# 2. Deploy to Kubernetes
./scripts/deploy.sh production v2.0.0

# 3. Verify deployment
kubectl get pods -n aaas
kubectl get svc -n aaas
```

#### Manual Deployment
```bash
# Apply manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl rollout status deployment/aaas-deployment -n aaas

# View logs
kubectl logs -f deployment/aaas-deployment -n aaas
```

#### Rollback
```bash
# Rollback to previous version
./scripts/rollback.sh

# Rollback to specific revision
./scripts/rollback.sh 3
```

---

### Option 2: Docker Compose (Recommended for Single Server)

#### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM recommended

#### Quick Start
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your values
nano .env

# 3. Start the stack
docker-compose -f docker-compose.prod.yml up -d

# 4. Check status
docker-compose -f docker-compose.prod.yml ps

# 5. View logs
docker-compose -f docker-compose.prod.yml logs -f aaas-api
```

#### What's Included
The production stack includes:
- **AaaS API**: Main application (3 replicas)
- **PostgreSQL**: Persistent database
- **Redis**: Caching and session storage
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **Nginx**: Reverse proxy with SSL
- **Alertmanager**: Alert routing
- **Node Exporter**: System metrics

#### Accessing Services
- **API**: https://localhost (or your domain)
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9091
- **Metrics**: http://localhost:9090/metrics

#### Maintenance
```bash
# Update to latest version
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# View resource usage
docker stats

# Backup database
docker exec aaas-postgres pg_dump -U aaas aaas > backup.sql

# Restore database
docker exec -i aaas-postgres psql -U aaas aaas < backup.sql

# Clean up old images
docker system prune -a
```

---

## Monitoring & Observability

### Prometheus Metrics
The following metrics are exposed at `/metrics`:

#### Agent Metrics
- `aaas_agents_created_total` - Total agents created
- `aaas_agents_deleted_total` - Total agents deleted
- `aaas_active_agents` - Current active agents by status
- `aaas_agent_uptime_seconds` - Agent uptime
- `aaas_agent_recoveries_total` - Successful recoveries

#### Message Metrics
- `aaas_messages_total` - Total messages processed
- `aaas_message_duration_seconds` - Message processing time

#### HTTP Metrics
- `aaas_http_requests_total` - Total HTTP requests
- `aaas_http_request_duration_seconds` - Request duration

#### System Metrics
- `aaas_system_memory_bytes` - Memory usage
- `aaas_system_cpu_percent` - CPU usage

#### Auto-scaling Metrics
- `aaas_autoscale_events_total` - Scaling events
- `aaas_autoscale_target_agents` - Target agent count

### Grafana Dashboards
Access Grafana at http://localhost:3000

**Pre-configured dashboards:**
1. **AaaS Overview**: Agent counts, request rates, system health
2. **Performance**: Response times, throughput, error rates
3. **Auto-scaling**: Scaling events, utilization, trends
4. **System Resources**: CPU, memory, disk usage

### Alerting
Alerts are configured in `monitoring/alertmanager.yml`

**Default alerts:**
- High error rate (>5%)
- Agent failures
- Memory usage >90%
- CPU usage >85%
- Auto-scaling failures

**Configure Slack alerts:**
```yaml
# In monitoring/alertmanager.yml
slack_configs:
  - api_url: 'YOUR_WEBHOOK_URL'
    channel: '#aaas-alerts'
```

---

## Security Checklist

### Before Production
- [ ] Generate strong API keys
- [ ] Configure SSL/TLS certificates
- [ ] Set secure database passwords
- [ ] Enable API key authentication
- [ ] Configure rate limiting
- [ ] Set up CORS properly
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Set up backup strategy
- [ ] Configure monitoring alerts

### SSL/TLS Setup
```bash
# Using certbot for Let's Encrypt
certbot certonly --standalone -d api.aaas.example.com

# Copy certificates to nginx
cp /etc/letsencrypt/live/api.aaas.example.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/api.aaas.example.com/privkey.pem nginx/ssl/key.pem
```

---

## Performance Tuning

### Kubernetes
```yaml
# In k8s/deployment.yaml
resources:
  limits:
    memory: "4Gi"  # Adjust based on load
    cpu: "2000m"
  requests:
    memory: "1Gi"
    cpu: "500m"

# HPA settings
spec:
  minReplicas: 3
  maxReplicas: 20  # Scale based on your needs
```

### Docker Compose
```yaml
# In docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 8G
```

### Application Settings
```bash
# In .env
MAX_AGENTS=100  # Increase for higher capacity
RATE_LIMIT_PER_MINUTE=200  # Adjust rate limits
SCALE_UP_THRESHOLD=0.7  # Lower for more aggressive scaling
```

---

## Troubleshooting

### Common Issues

**Agents not starting**
```bash
# Check logs
kubectl logs -f deployment/aaas-deployment -n aaas
# or
docker-compose logs -f aaas-api

# Check environment variables
kubectl describe pod -n aaas
# or
docker-compose config
```

**High memory usage**
```bash
# Reduce max agents
kubectl set env deployment/aaas-deployment MAX_AGENTS=30 -n aaas

# Or update .env
MAX_AGENTS=30
docker-compose -f docker-compose.prod.yml up -d
```

**Database connection issues**
```bash
# Check PostgreSQL
kubectl exec -it deployment/aaas-deployment -n aaas -- \
  psql -h postgres -U aaas -d aaas
# or
docker exec -it aaas-postgres psql -U aaas
```

**Auto-scaling not working**
```bash
# Check autoscaler stats
curl http://localhost:8000/autoscaler/stats

# View autoscaler logs
kubectl logs -f deployment/aaas-deployment -n aaas | grep -i autoscal
```

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Metrics
curl http://localhost:9090/metrics

# Autoscaler stats
curl http://localhost:8000/autoscaler/stats
```

---

## Backup & Recovery

### Database Backup
```bash
# Automated daily backup (add to cron)
0 2 * * * docker exec aaas-postgres pg_dump -U aaas aaas | gzip > /backups/aaas-$(date +\%Y\%m\%d).sql.gz
```

### Full System Backup
```bash
# Backup volumes
docker run --rm -v aaas_postgres_data:/data -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres-data.tar.gz /data

# Backup configurations
tar czf backup-configs.tar.gz k8s/ monitoring/ nginx/ .env
```

### Disaster Recovery
```bash
# Restore database
gunzip -c backup.sql.gz | docker exec -i aaas-postgres psql -U aaas aaas

# Restore configurations
tar xzf backup-configs.tar.gz

# Redeploy
./scripts/deploy.sh production v2.0.0
```

---

## Scaling Guidelines

### Vertical Scaling (More Resources)
Increase resources per pod/container:
```yaml
resources:
  limits:
    memory: "8Gi"
    cpu: "4000m"
```

### Horizontal Scaling (More Pods)
Increase replica count:
```bash
kubectl scale deployment aaas-deployment --replicas=10 -n aaas
```

Or configure HPA:
```yaml
spec:
  minReplicas: 5
  maxReplicas: 50
  targetCPUUtilizationPercentage: 60
```

### Application Scaling (More Agents)
Increase agent capacity:
```bash
# In .env or ConfigMap
MAX_AGENTS=200
MIN_AGENTS=10
```

---

## Cost Optimization

### Reduce Costs
1. **Enable auto-scaling**: Automatically scales down during low traffic
2. **Use spot instances**: For Kubernetes nodes (AWS/GCP)
3. **Optimize agent timeout**: Lower idle timeout to free resources
4. **Use Redis caching**: Reduce database queries
5. **Enable metrics pruning**: Clean old metrics data

### Monitor Costs
```bash
# Track agent usage
curl http://localhost:8000/autoscaler/stats

# View resource utilization
kubectl top pods -n aaas
# or
docker stats
```

---

## Support

For issues or questions:
1. Check logs and metrics
2. Review troubleshooting section
3. Open an issue on GitHub (for licensed users)

---

## License

**PROPRIETARY - CLOSED SOURCE**

This software is proprietary and confidential. See LICENSE file for details.

Copyright (c) 2025 WilBtc. All rights reserved.
