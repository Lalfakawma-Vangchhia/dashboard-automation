"""
Performance optimization utilities for the Automation Dashboard.
"""
import asyncio
import time
import logging
from typing import Any, Callable, Dict, Optional
from functools import wraps
from cachetools import TTLCache
import threading

logger = logging.getLogger(__name__)

# Global caches
_memory_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes
_rate_limit_cache = TTLCache(maxsize=100, ttl=60)  # 1 minute
_lock = threading.Lock()


def rate_limit(max_calls: int = 10, time_window: int = 60):
    """
    Rate limiting decorator for API calls.
    
    Args:
        max_calls: Maximum number of calls allowed in the time window
        time_window: Time window in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            current_time = time.time()
            
            with _lock:
                if func_name not in _rate_limit_cache:
                    _rate_limit_cache[func_name] = []
                
                # Clean old timestamps
                _rate_limit_cache[func_name] = [
                    ts for ts in _rate_limit_cache[func_name] 
                    if current_time - ts < time_window
                ]
                
                # Check if we're over the limit
                if len(_rate_limit_cache[func_name]) >= max_calls:
                    wait_time = time_window - (current_time - _rate_limit_cache[func_name][0])
                    logger.warning(f"Rate limit exceeded for {func_name}, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                
                # Add current timestamp
                _rate_limit_cache[func_name].append(current_time)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def cache_result(ttl: int = 300):
    """
    Cache decorator for function results.
    
    Args:
        ttl: Time to live in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            args_str = str(args)
            kwargs_str = str(sorted(kwargs.items()))
            cache_key = f"{func.__name__}:{hash(args_str + kwargs_str)}"
            
            # Check cache
            if cache_key in _memory_cache:
                logger.debug(f"Cache hit for {func.__name__}")
                return _memory_cache[cache_key]
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            _memory_cache[cache_key] = result
            return result
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Retry decorator for failed operations.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (doubles each retry)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        await asyncio.sleep(current_delay)
                        current_delay *= 2
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
                        raise last_exception
            
            raise last_exception
        return wrapper
    return decorator


def measure_performance(func: Callable) -> Callable:
    """
    Performance measurement decorator.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    return wrapper


class ConnectionPool:
    """Simple connection pool for database and external API connections."""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections = []
        self.lock = asyncio.Lock()
    
    async def get_connection(self):
        """Get a connection from the pool."""
        async with self.lock:
            if self.connections:
                return self.connections.pop()
            return None
    
    async def return_connection(self, connection):
        """Return a connection to the pool."""
        async with self.lock:
            if len(self.connections) < self.max_connections:
                self.connections.append(connection)


def clear_caches():
    """Clear all caches."""
    _memory_cache.clear()
    _rate_limit_cache.clear()
    logger.info("All caches cleared")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return {
        "memory_cache_size": len(_memory_cache),
        "memory_cache_maxsize": _memory_cache.maxsize,
        "rate_limit_cache_size": len(_rate_limit_cache),
        "rate_limit_cache_maxsize": _rate_limit_cache.maxsize
    } 