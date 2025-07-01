"""
Rate Limiter Module

This module provides a decorator for rate limiting API endpoints.
It uses a simple in-memory implementation with window-based rate limiting.

Usage:
    from utils.rate_limiter import ratelimit

    @app.route('/api/endpoint')
    @ratelimit(limit="30/minute")
    def api_endpoint():
        ...
"""

import time
from functools import wraps
from flask import request, jsonify, current_app
from collections import defaultdict, deque

# Store for rate limiting
# Structure: {ip_addr: {endpoint: deque([timestamps])}}
request_store = defaultdict(lambda: defaultdict(deque))

def ratelimit(limit="30/minute", by="ip"):
    """
    Rate limiting decorator that limits requests based on IP address.
    
    Args:
        limit (str): Rate limit in format "<count>/<period>", e.g., "30/minute"
        by (str): Limit by "ip" (IP address) or "endpoint" (API endpoint)
        
    Returns:
        decorator: Function that can be used to decorate routes
    """
    try:
        count, period = limit.split("/")
        count = int(count)
    except (ValueError, TypeError):
        raise ValueError("Invalid rate limit format. Use '<count>/<period>'")
    
    # Convert period to seconds
    periods = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "day": 86400
    }
    
    if period not in periods:
        raise ValueError(f"Invalid time period. Use one of {list(periods.keys())}")
        
    period_seconds = periods[period]
    
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get identifier based on rate limiting strategy
            if by == "ip":
                key = request.remote_addr or "unknown"
            else:
                key = request.endpoint
                
            # Get current endpoint
            endpoint = request.endpoint
            
            # Get current time
            now = time.time()
            
            # Clean up old timestamps
            while (
                request_store[key][endpoint] and 
                request_store[key][endpoint][0] < now - period_seconds
            ):
                request_store[key][endpoint].popleft()
            
            # Check if we're over the limit
            if len(request_store[key][endpoint]) >= count:
                response = jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit is {count} requests per {period}."
                })
                response.status_code = 429
                retry_after = int(
                    period_seconds - (now - request_store[key][endpoint][0])
                )
                response.headers['Retry-After'] = max(1, retry_after)
                return response
            
            # Add current timestamp
            request_store[key][endpoint].append(now)
            
            # Call the original function
            return f(*args, **kwargs)
        
        return wrapped
    
    return decorator
