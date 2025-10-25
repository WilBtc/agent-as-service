"""
Prometheus metrics for AaaS monitoring
"""

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest
from fastapi import Response
import time
from functools import wraps
from typing import Callable
import logging

logger = logging.getLogger(__name__)


# Application info
app_info = Info('aaas_app', 'Application information')
app_info.info({
    'version': '2.0.0',
    'platform': 'Agent as a Service'
})


# Agent metrics
agent_create_counter = Counter(
    'aaas_agents_created_total',
    'Total number of agents created',
    ['agent_type', 'auto_start']
)

agent_delete_counter = Counter(
    'aaas_agents_deleted_total',
    'Total number of agents deleted',
    ['reason']
)

agent_start_counter = Counter(
    'aaas_agents_started_total',
    'Total number of agents started',
    ['agent_type']
)

agent_stop_counter = Counter(
    'aaas_agents_stopped_total',
    'Total number of agents stopped'
)

agent_error_counter = Counter(
    'aaas_agent_errors_total',
    'Total number of agent errors',
    ['error_type', 'agent_type']
)

agent_recovery_counter = Counter(
    'aaas_agent_recoveries_total',
    'Total number of successful agent recoveries',
    ['agent_type']
)

agent_recovery_failure_counter = Counter(
    'aaas_agent_recovery_failures_total',
    'Total number of failed agent recoveries',
    ['agent_type']
)

active_agents_gauge = Gauge(
    'aaas_active_agents',
    'Number of currently active agents',
    ['status', 'agent_type']
)

agent_uptime_gauge = Gauge(
    'aaas_agent_uptime_seconds',
    'Agent uptime in seconds',
    ['agent_id', 'agent_type']
)

agent_idle_time_gauge = Gauge(
    'aaas_agent_idle_seconds',
    'Time since agent last activity',
    ['agent_id']
)


# Message metrics
message_counter = Counter(
    'aaas_messages_total',
    'Total number of messages processed',
    ['agent_type', 'status']
)

message_duration_histogram = Histogram(
    'aaas_message_duration_seconds',
    'Time spent processing messages',
    ['agent_type'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0)
)

message_tokens_histogram = Histogram(
    'aaas_message_tokens',
    'Number of tokens in messages',
    ['agent_type', 'direction'],
    buckets=(10, 50, 100, 500, 1000, 2000, 4000, 8000)
)


# HTTP metrics
http_requests_counter = Counter(
    'aaas_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_histogram = Histogram(
    'aaas_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)


# Rate limiting metrics
rate_limit_exceeded_counter = Counter(
    'aaas_rate_limit_exceeded_total',
    'Number of rate limit exceeded events',
    ['endpoint']
)


# System metrics
system_memory_usage_gauge = Gauge(
    'aaas_system_memory_bytes',
    'System memory usage in bytes',
    ['type']
)

system_cpu_usage_gauge = Gauge(
    'aaas_system_cpu_percent',
    'System CPU usage percentage'
)


# Auto-scaling metrics
autoscale_event_counter = Counter(
    'aaas_autoscale_events_total',
    'Number of autoscaling events',
    ['direction', 'reason']
)

autoscale_agents_gauge = Gauge(
    'aaas_autoscale_target_agents',
    'Target number of agents from autoscaler'
)


# Health check metrics
health_check_counter = Counter(
    'aaas_health_checks_total',
    'Total number of health checks',
    ['status']
)

unhealthy_agents_gauge = Gauge(
    'aaas_unhealthy_agents',
    'Number of unhealthy agents'
)


def track_agent_creation(agent_type: str, auto_start: bool):
    """Track agent creation"""
    agent_create_counter.labels(
        agent_type=agent_type,
        auto_start=str(auto_start)
    ).inc()


def track_agent_deletion(reason: str = "user_requested"):
    """Track agent deletion"""
    agent_delete_counter.labels(reason=reason).inc()


def track_agent_start(agent_type: str):
    """Track agent start"""
    agent_start_counter.labels(agent_type=agent_type).inc()


def track_agent_stop():
    """Track agent stop"""
    agent_stop_counter.inc()


def track_agent_error(error_type: str, agent_type: str):
    """Track agent error"""
    agent_error_counter.labels(
        error_type=error_type,
        agent_type=agent_type
    ).inc()


def track_agent_recovery(agent_type: str, success: bool):
    """Track agent recovery attempt"""
    if success:
        agent_recovery_counter.labels(agent_type=agent_type).inc()
    else:
        agent_recovery_failure_counter.labels(agent_type=agent_type).inc()


def update_active_agents(status: str, agent_type: str, count: int):
    """Update active agents gauge"""
    active_agents_gauge.labels(
        status=status,
        agent_type=agent_type
    ).set(count)


def track_message(agent_type: str, status: str, duration: float):
    """Track message processing"""
    message_counter.labels(
        agent_type=agent_type,
        status=status
    ).inc()

    message_duration_histogram.labels(
        agent_type=agent_type
    ).observe(duration)


def track_http_request(method: str, endpoint: str, status: int, duration: float):
    """Track HTTP request"""
    http_requests_counter.labels(
        method=method,
        endpoint=endpoint,
        status=str(status)
    ).inc()

    http_request_duration_histogram.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_rate_limit_exceeded(endpoint: str):
    """Track rate limit exceeded"""
    rate_limit_exceeded_counter.labels(endpoint=endpoint).inc()


def track_autoscale_event(direction: str, reason: str):
    """Track autoscaling event"""
    autoscale_event_counter.labels(
        direction=direction,
        reason=reason
    ).inc()


def track_health_check(status: str):
    """Track health check"""
    health_check_counter.labels(status=status).inc()


def timer(metric_func: Callable):
    """Decorator to time function execution and track metrics"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metric_func(duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metric_func(duration, success=False)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metric_func(duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metric_func(duration, success=False)
                raise

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def get_metrics() -> Response:
    """Generate Prometheus metrics response"""
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


# System monitoring functions
def update_system_metrics():
    """Update system-level metrics"""
    try:
        import psutil

        # Memory metrics
        memory = psutil.virtual_memory()
        system_memory_usage_gauge.labels(type='used').set(memory.used)
        system_memory_usage_gauge.labels(type='available').set(memory.available)
        system_memory_usage_gauge.labels(type='total').set(memory.total)

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        system_cpu_usage_gauge.set(cpu_percent)

    except ImportError:
        logger.warning("psutil not installed, system metrics unavailable")
    except Exception as e:
        logger.error(f"Error updating system metrics: {e}")
