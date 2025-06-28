"""
Performance optimization utilities
"""
import time
from functools import wraps

def cache_results(ttl: int = 300):
    """Decorator to cache function results for a specified TTL (seconds)"""
    cache = {}

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = (args, frozenset(kwargs.items()))
            now = time.time()

            # Check if result is in cache and not expired
            if key in cache:
                stored_time, result = cache[key]
                if now - stored_time < ttl:
                    return result

            # Call the function and cache the result
            result = await func(*args, **kwargs)
            cache[key] = (now, result)

            return result

        return wrapper

    return decorator

def async_timeout(seconds: int):
    """Decorator to add timeout to an async function"""
    import asyncio

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")

        return wrapper

    return decorator