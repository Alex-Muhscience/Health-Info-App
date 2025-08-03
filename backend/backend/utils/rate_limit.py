"""
Simple rate limiting utility
"""

import hashlib

def rate_limit_key(identifier: str) -> str:
    """Generate rate limiting key"""
    return f"rate_limit:{hashlib.sha256(identifier.encode()).hexdigest()}"

