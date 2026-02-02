# app/services/cache.py
"""
Redis caching service for performance optimization.
Provides async caching for frequently accessed data.
"""
import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import redis.asyncio as redis
from ..config import settings

# Redis client (initialized lazily)
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> Optional[redis.Redis]:
    """Get or create Redis connection."""
    global _redis_client
    
    if _redis_client is None:
        redis_url = getattr(settings, "REDIS_URL", None)
        if redis_url:
            try:
                _redis_client = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection
                await _redis_client.ping()
                print("✅ Redis connected successfully")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}")
                _redis_client = None
        else:
            print("⚠️ REDIS_URL not configured, caching disabled")
    
    return _redis_client


class CacheKeys:
    """Cache key prefixes for different data types."""
    KB_ARTICLE = "kb:article:"
    KB_LIST = "kb:list:"
    TICKET = "ticket:"
    ANALYTICS = "analytics:"
    VECTOR_SEARCH = "vector:search:"
    USER = "user:"


class CacheTTL:
    """Default TTL values in seconds."""
    KB_ARTICLE = 300      # 5 minutes
    KB_LIST = 180         # 3 minutes
    ANALYTICS = 60        # 1 minute
    VECTOR_SEARCH = 60    # 1 minute
    USER = 600            # 10 minutes


async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    client = await get_redis()
    if client is None:
        return None
    
    try:
        value = await client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        print(f"Cache get error: {e}")
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """Set value in cache with TTL."""
    client = await get_redis()
    if client is None:
        return False
    
    try:
        await client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """Delete key from cache."""
    client = await get_redis()
    if client is None:
        return False
    
    try:
        await client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False


async def cache_delete_pattern(pattern: str) -> int:
    """Delete all keys matching pattern."""
    client = await get_redis()
    if client is None:
        return 0
    
    try:
        keys = await client.keys(pattern)
        if keys:
            return await client.delete(*keys)
    except Exception as e:
        print(f"Cache delete pattern error: {e}")
    return 0


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()[:16]


def cached(prefix: str, ttl: int = 300):
    """
    Decorator for caching async function results.
    
    Usage:
        @cached(CacheKeys.KB_ARTICLE, CacheTTL.KB_ARTICLE)
        async def get_kb_article(article_id: int):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{prefix}{generate_cache_key(*args, **kwargs)}"
            
            # Try cache first
            cached_value = await cache_get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                await cache_set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
