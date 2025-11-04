"""
Redis caching for API responses and frequently accessed data.
"""

from typing import Optional, Any
import json
import hashlib
from api.config import REDIS_ENABLED, REDIS_URL
import os
from api.logger import logger

# Try to import redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# Global Redis client
_redis_client: Optional[Any] = None


def get_redis_client():
    """Get or create Redis client."""
    global _redis_client
    
    # Redis is optional - if not enabled or not available, return None (graceful degradation)
    if not REDIS_ENABLED:
        return None
    
    if not REDIS_AVAILABLE:
        return None
    
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            # Test connection
            _redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            _redis_client = None
            return None
    
    return _redis_client


def generate_cache_key(prefix: str, **kwargs) -> str:
    """Generate a cache key from parameters."""
    # Sort kwargs to ensure consistent keys
    sorted_params = sorted(kwargs.items())
    params_str = json.dumps(sorted_params, sort_keys=True)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
    return f"{prefix}:{params_hash}"


async def get_cached(key: str) -> Optional[Any]:
    """Get value from cache."""
    client = get_redis_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
    
    return None


async def set_cached(key: str, value: Any, ttl: int = 300) -> bool:
    """Set value in cache with TTL (default 5 minutes)."""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.warning(f"Cache set error: {e}")
        return False


async def delete_cached(key: str) -> bool:
    """Delete value from cache."""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete error: {e}")
        return False


async def clear_cache_pattern(pattern: str) -> int:
    """Clear all cache keys matching pattern."""
    client = get_redis_client()
    if not client:
        return 0
    
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"Cache clear error: {e}")
        return 0

