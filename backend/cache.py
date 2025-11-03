"""
Redis cache management for performance optimization
"""
import json
import logging
import asyncio
from typing import Any, Optional
from functools import wraps
import redis
from redis import Redis

from config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self._connect()

    def _connect(self):
        """Establish Redis connection"""
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Redis initialization error: {e}")
            self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.redis_client:
            return False

        try:
            serialized_value = json.dumps(value)
            ttl = ttl or settings.redis_cache_ttl
            return bool(self.redis_client.setex(key, ttl, serialized_value))
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

# Global cache instance
cache = CacheManager()

def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator to cache function results
    """
    def decorator(func):
        def build_cache_key(call_args, call_kwargs):
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in call_args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(call_kwargs.items()))
            return ":".join(key_parts)

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                cache_key = build_cache_key(args, kwargs)
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result

                result = await func(*args, **kwargs)
                if result is not None:
                    cache.set(cache_key, result, ttl)
                    logger.debug(f"Cached result for {cache_key}")
                return result
            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = build_cache_key(args, kwargs)
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            result = func(*args, **kwargs)
            if result is not None:
                cache.set(cache_key, result, ttl)
                logger.debug(f"Cached result for {cache_key}")
            return result

        return sync_wrapper
    return decorator

def invalidate_cache_pattern(pattern: str):
    """Invalidate cache keys matching pattern"""
    cleared = cache.clear_pattern(pattern)
    if cleared > 0:
        logger.info(f"Invalidated {cleared} cache entries matching {pattern}")
    return cleared
