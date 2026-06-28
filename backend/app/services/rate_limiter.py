from redis import Redis

from app.core.config import settings
from app.core.exceptions import AppError


class RateLimiter:
    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client

    def check(self, key: str) -> None:
        current = self.redis_client.incr(key)
        if current == 1:
            self.redis_client.expire(key, settings.auth_rate_limit_window_seconds)
        if current > settings.auth_rate_limit_attempts:
            raise AppError("RATE_LIMITED", "Too many attempts. Try again later.", 429)
