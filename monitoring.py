"""Monitoring and metrics collection for Telegram Ollama Bot"""

import time
import psutil
import logging
from typing import Dict, Any
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import os

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'telegram_bot_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

RESPONSE_TIME = Histogram(
    'telegram_bot_response_time_seconds',
    'Response time in seconds',
    ['method', 'endpoint']
)

ACTIVE_USERS = Gauge(
    'telegram_bot_active_users',
    'Number of active users in the last 24 hours'
)

MESSAGE_COUNT = Counter(
    'telegram_bot_messages_total',
    'Total number of messages processed',
    ['type', 'status']  # type: text, image, voice, etc.; status: success, error
)

AI_REQUESTS = Counter(
    'telegram_bot_ai_requests_total',
    'Total number of AI requests',
    ['model', 'status']
)

AI_RESPONSE_TIME = Histogram(
    'telegram_bot_ai_response_time_seconds',
    'AI response time in seconds',
    ['model']
)

MEMORY_USAGE = Gauge(
    'telegram_bot_memory_usage_bytes',
    'Current memory usage in bytes'
)

CPU_USAGE = Gauge(
    'telegram_bot_cpu_usage_percent',
    'Current CPU usage percentage'
)

OLLAMA_STATUS = Gauge(
    'telegram_bot_ollama_status',
    'Ollama service status (1=up, 0=down)'
)

def track_request(method: str, endpoint: str):
    """Decorator to track API requests"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                REQUEST_COUNT.labels(method=method, endpoint=endpoint, status='success').inc()
                RESPONSE_TIME.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
                return result
            except Exception as e:
                REQUEST_COUNT.labels(method=method, endpoint=endpoint, status='error').inc()
                RESPONSE_TIME.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
                raise e
        return wrapper
    return decorator

def track_message(message_type: str):
    """Decorator to track message processing"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                MESSAGE_COUNT.labels(type=message_type, status='success').inc()
                return result
            except Exception as e:
                MESSAGE_COUNT.labels(type=message_type, status='error').inc()
                raise e
        return wrapper
    return decorator

def track_ai_request(model: str):
    """Decorator to track AI requests"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                AI_REQUESTS.labels(model=model, status='success').inc()
                AI_RESPONSE_TIME.labels(model=model).observe(time.time() - start_time)
                return result
            except Exception as e:
                AI_REQUESTS.labels(model=model, status='error').inc()
                AI_RESPONSE_TIME.labels(model=model).observe(time.time() - start_time)
                raise e
        return wrapper
    return decorator

class SystemMonitor:
    """System resource monitoring"""

    def __init__(self):
        self.process = psutil.Process()
        self.last_update = 0
        self.update_interval = 30  # Update every 30 seconds

    def update_metrics(self):
        """Update system metrics"""
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return

        try:
            # Memory usage
            memory_info = self.process.memory_info()
            MEMORY_USAGE.set(memory_info.rss)

            # CPU usage (over 1 second interval)
            cpu_percent = self.process.cpu_percent(interval=1.0)
            CPU_USAGE.set(cpu_percent)

            self.last_update = current_time

        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")

class HealthChecker:
    """Health check functionality"""

    def __init__(self, ollama_host: str = "http://buntcomm.com:11434"):
        self.ollama_host = ollama_host
        self.last_check = 0
        self.check_interval = 60  # Check every 60 seconds

    async def check_ollama_health(self) -> bool:
        """Check if Ollama service is healthy"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_host}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        OLLAMA_STATUS.set(1)
                        return True
                    else:
                        OLLAMA_STATUS.set(0)
                        return False
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            OLLAMA_STATUS.set(0)
            return False

    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "checks": {}
        }

        # Check Ollama
        ollama_healthy = await self.check_ollama_health()
        health_status["checks"]["ollama"] = {
            "status": "healthy" if ollama_healthy else "unhealthy",
            "details": f"Ollama service at {self.ollama_host}"
        }

        # Check database (if implemented)
        try:
            from database import get_db
            db = next(get_db())
            db.execute("SELECT 1")
            health_status["checks"]["database"] = {
                "status": "healthy",
                "details": "Database connection successful"
            }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "details": f"Database error: {str(e)}"
            }
            health_status["status"] = "degraded"

        # Check system resources
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)

            health_status["checks"]["system"] = {
                "status": "healthy",
                "details": f"Memory: {memory.percent}%, CPU: {cpu}%"
            }

            if memory.percent > 90 or cpu > 95:
                health_status["status"] = "warning"

        except Exception as e:
            health_status["checks"]["system"] = {
                "status": "unhealthy",
                "details": f"System check error: {str(e)}"
            }

        # Set overall status
        if any(check["status"] == "unhealthy" for check in health_status["checks"].values()):
            health_status["status"] = "unhealthy"

        return health_status

def get_metrics():
    """Get current metrics in Prometheus format"""
    return generate_latest()

# Global instances
system_monitor = SystemMonitor()
health_checker = HealthChecker()

# Export for use in other modules
__all__ = [
    'track_request',
    'track_message',
    'track_ai_request',
    'system_monitor',
    'health_checker',
    'get_metrics'
]