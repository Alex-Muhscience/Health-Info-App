import time
from functools import wraps
from typing import Dict, Tuple, Callable, Optional, Union, Any
from flask import request, g


class RateLimiter:
    """
    Rate limiting utility for API endpoints
    """
    _store: Dict[str, Dict[str, Union[int, float]]] = {}

    @classmethod
    def limit(cls, requests: int = 100, window: int = 900, by: str = 'ip') -> Callable:
        """
        Decorator to rate limit API endpoints

        Args:
            requests: Number of allowed requests per window
            window: Time window in seconds (default 15 minutes)
            by: What to limit by ('ip', 'user', or 'endpoint')

        Returns:
            Decorator function
        """

        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapped(*args: Any, **kwargs: Any) -> Union[Tuple[Dict[str, str], int], Any]:
                # Get the limiting key
                key: str
                if by == 'ip':
                    key = request.remote_addr or 'unknown'
                elif by == 'user' and hasattr(g, 'user'):
                    key = str(getattr(g.user, 'id', 'unknown'))
                else:  # by endpoint
                    key = f"{request.method}:{request.path}"

                # Get current timestamp
                now = time.time()

                # Initialize if not exists
                if key not in cls._store:
                    cls._store[key] = {'count': 0, 'start': now}

                # Reset if window has passed
                if now - cls._store[key]['start'] > window:  # type: ignore
                    cls._store[key] = {'count': 1, 'start': now}
                else:
                    cls._store[key]['count'] += 1  # type: ignore

                # Check if limit exceeded
                if cls._store[key]['count'] > requests:  # type: ignore
                    return {
                        "error": "rate_limit_exceeded",
                        "message": f"Too many requests. Limit {requests} per {window} seconds."
                    }, 429

                return f(*args, **kwargs)

            return wrapped

        return decorator


class ConcurrencyLimiter:
    """
    Concurrency limiting utility
    """
    _active_requests: Dict[str, int] = {}
    _max_concurrent: int = 50

    @classmethod
    def concurrency_limit(cls, f: Callable) -> Callable:
        """
        Decorator to limit concurrent requests

        Args:
            f: The function to decorate

        Returns:
            Decorated function
        """

        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any) -> Union[Tuple[Dict[str, str], int], Any]:
            endpoint = f"{request.method}:{request.path}"

            # Check total concurrent requests
            if sum(cls._active_requests.values()) >= cls._max_concurrent:
                return {"error": "too_busy", "message": "Server at capacity"}, 503

            # Increment counter for this endpoint
            cls._active_requests[endpoint] = cls._active_requests.get(endpoint, 0) + 1

            try:
                return f(*args, **kwargs)
            finally:
                # Decrement counter when request completes
                cls._active_requests[endpoint] -= 1
                if cls._active_requests[endpoint] <= 0:
                    del cls._active_requests[endpoint]

        return wrapped


class MaintenanceMode:
    """
    Maintenance mode checker
    """
    _maintenance_mode: bool = False
    _allowed_ips: list[str] = []
    _bypass_tokens: list[str] = []

    @classmethod
    def check_maintenance(cls, f: Callable) -> Callable:
        """
        Decorator to check maintenance mode

        Args:
            f: The function to decorate

        Returns:
            Decorated function
        """

        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any) -> Union[Tuple[Dict[str, str], int], Any]:
            if cls._maintenance_mode:
                # Allow bypass for certain IPs or tokens
                remote_addr = request.remote_addr or ''
                bypass_token = request.headers.get('X-Bypass-Maintenance', '')

                if (remote_addr in cls._allowed_ips or
                        bypass_token in cls._bypass_tokens):
                    return f(*args, **kwargs)
                return {"error": "maintenance_mode"}, 503
            return f(*args, **kwargs)

        return wrapped

    @classmethod
    def set_mode(cls, enabled: bool,
                 allowed_ips: Optional[list[str]] = None,
                 bypass_tokens: Optional[list[str]] = None) -> None:
        """
        Set maintenance mode configuration

        Args:
            enabled: Whether maintenance mode is active
            allowed_ips: List of IPs that can bypass maintenance
            bypass_tokens: List of tokens that can bypass maintenance
        """
        cls._maintenance_mode = enabled
        if allowed_ips is not None:
            cls._allowed_ips = allowed_ips
        if bypass_tokens is not None:
            cls._bypass_tokens = bypass_tokens