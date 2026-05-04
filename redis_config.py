"""
redis_config.py
---------------
Central Redis connection settings and queue key names shared by all clients.
"""

import redis

REDIS_HOST: str = "localhost"
REDIS_PORT: int = 6379
REDIS_DB: int = 0

TEMPERATURE_QUEUE_KEY: str = "temperature_queue"
ALERT_QUEUE_KEY: str = "alert_queue"


def make_redis_client() -> redis.Redis:
    """Return a Redis client connected to the configured server."""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
