import secrets
print("JWT_SECRET_KEY=" + secrets.token_urlsafe(32))
print("JWT_REFRESH_SECRET_KEY=" + secrets.token_urlsafe(32))