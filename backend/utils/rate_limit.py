from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize Flask-Limiter
limiter = Limiter(
    key_func=get_remote_address,  # Use the client's IP address as the key
    storage_uri="redis://localhost:6379",  # Use Redis for production
    strategy="fixed-window",  # Rate-limiting strategy
)