#!/usr/bin/env python3
"""
Rate limiting middleware and utilities for API endpoints.
"""

from fastapi import Request, HTTPException, status
from typing import Dict, Optional, Callable
import time
import threading
import structlog
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Setup structured logging
log = structlog.get_logger()


@dataclass
class RateLimitInfo:
    """Information about rate limit state for a client."""
    
    requests: int = 0
    window_start: float = field(default_factory=time.time)
    last_request: float = field(default_factory=time.time)
    
    def reset_if_needed(self, window_duration: int) -> None:
        """Reset the rate limit window if it has expired."""
        current_time = time.time()
        if current_time - self.window_start >= window_duration:
            self.requests = 0
            self.window_start = current_time
    
    def add_request(self) -> None:
        """Record a new request."""
        self.requests += 1
        self.last_request = time.time()


class RateLimiter:
    """
    In-memory rate limiter with configurable limits and time windows.
    
    This is a simple implementation suitable for single-instance deployments.
    For production multi-instance deployments, consider using Redis-based rate limiting.
    """
    
    def __init__(self):
        self._clients: Dict[str, RateLimitInfo] = {}
        self._lock = threading.Lock()
    
    def is_allowed(
        self,
        client_id: str,
        limit: int,
        window_duration: int
    ) -> tuple[bool, int, int]:
        """
        Check if a request is allowed based on rate limits.
        
        Args:
            client_id: Unique identifier for the client (e.g., IP address)
            limit: Maximum number of requests allowed in the time window
            window_duration: Time window duration in seconds
            
        Returns:
            Tuple of (is_allowed, remaining_requests, reset_time_seconds)
        """
        with self._lock:
            current_time = time.time()
            
            # Get or create client info
            if client_id not in self._clients:
                self._clients[client_id] = RateLimitInfo()
            
            client_info = self._clients[client_id]
            
            # Reset window if needed
            client_info.reset_if_needed(window_duration)
            
            # Check if limit exceeded
            if client_info.requests >= limit:
                remaining = 0
                reset_time = int(client_info.window_start + window_duration - current_time)
                return False, remaining, max(reset_time, 0)
            
            # Allow request and update counters
            client_info.add_request()
            remaining = max(limit - client_info.requests, 0)
            reset_time = int(client_info.window_start + window_duration - current_time)
            
            return True, remaining, max(reset_time, 0)
    
    def cleanup_expired_clients(self, max_idle_time: int = 3600) -> None:
        """
        Clean up client records that haven't been active for a while.
        
        Args:
            max_idle_time: Maximum idle time in seconds before cleanup
        """
        with self._lock:
            current_time = time.time()
            expired_clients = [
                client_id for client_id, info in self._clients.items()
                if current_time - info.last_request > max_idle_time
            ]
            
            for client_id in expired_clients:
                del self._clients[client_id]
            
            if expired_clients:
                log.info(
                    "rate_limiter_cleanup",
                    expired_clients_count=len(expired_clients),
                    remaining_clients_count=len(self._clients)
                )


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_client_id(request: Request) -> str:
    """
    Extract a unique client identifier from the request.
    
    Priority order:
    1. X-Real-IP header (from reverse proxy)
    2. X-Forwarded-For header (first IP)
    3. Client IP from request
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client identifier string
    """
    # Check for real IP header (from reverse proxy)
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    
    # Check for forwarded IP header
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    # Fall back to client IP
    if request.client:
        return request.client.host
    
    # Last resort
    return "unknown"


def rate_limit(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000
) -> Callable:
    """
    Rate limiting decorator for FastAPI endpoints.
    
    Args:
        requests_per_minute: Maximum requests per minute per client
        requests_per_hour: Maximum requests per hour per client
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Extract request object from arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Look in kwargs
                request = kwargs.get('request')
            
            if not request:
                log.warning("rate_limit_no_request", function=func.__name__)
                # If we can't find request, allow the call
                return await func(*args, **kwargs)
            
            client_id = get_client_id(request)
            correlation_id = getattr(request.scope, 'correlation_id', 'unknown')
            
            # Check minute-based rate limit
            allowed_minute, remaining_minute, reset_minute = _rate_limiter.is_allowed(
                f"{client_id}:minute",
                requests_per_minute,
                60
            )
            
            if not allowed_minute:
                log.warning(
                    "rate_limit_exceeded_minute",
                    client_id=client_id,
                    correlation_id=correlation_id,
                    limit=requests_per_minute,
                    reset_in_seconds=reset_minute
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded: {requests_per_minute} requests per minute",
                        "correlation_id": correlation_id,
                        "retry_after_seconds": reset_minute
                    },
                    headers={
                        "X-RateLimit-Limit": str(requests_per_minute),
                        "X-RateLimit-Remaining": str(remaining_minute),
                        "X-RateLimit-Reset": str(int(time.time()) + reset_minute),
                        "Retry-After": str(reset_minute)
                    }
                )
            
            # Check hour-based rate limit
            allowed_hour, remaining_hour, reset_hour = _rate_limiter.is_allowed(
                f"{client_id}:hour",
                requests_per_hour,
                3600
            )
            
            if not allowed_hour:
                log.warning(
                    "rate_limit_exceeded_hour",
                    client_id=client_id,
                    correlation_id=correlation_id,
                    limit=requests_per_hour,
                    reset_in_seconds=reset_hour
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded: {requests_per_hour} requests per hour",
                        "correlation_id": correlation_id,
                        "retry_after_seconds": reset_hour
                    },
                    headers={
                        "X-RateLimit-Limit": str(requests_per_hour),
                        "X-RateLimit-Remaining": str(remaining_hour),
                        "X-RateLimit-Reset": str(int(time.time()) + reset_hour),
                        "Retry-After": str(reset_hour)
                    }
                )
            
            # Log successful rate limit check
            log.debug(
                "rate_limit_allowed",
                client_id=client_id,
                correlation_id=correlation_id,
                remaining_minute=remaining_minute,
                remaining_hour=remaining_hour
            )
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def cleanup_rate_limiter() -> None:
    """Clean up expired rate limiter entries. Should be called periodically."""
    _rate_limiter.cleanup_expired_clients()