import secrets

import redis
from django.conf import settings

VERIFY_EMAIL_PREFIX = "verify_email:"
PASSWORD_RESET_PREFIX = "password_reset:"

_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_redis_client():
    return _client


def create_verification_token(user_id) -> str:
    token = secrets.token_urlsafe(32)
    client = get_redis_client()
    client.setex(
        f"{VERIFY_EMAIL_PREFIX}{token}",
        settings.EMAIL_VERIFICATION_TTL,
        str(user_id),
    )
    return token


def get_user_id_from_verification_token(token: str) -> str | None:
    client = get_redis_client()
    user_id = client.get(f"{VERIFY_EMAIL_PREFIX}{token}")
    return user_id


def delete_verification_token(token: str) -> None:
    client = get_redis_client()
    client.delete(f"{VERIFY_EMAIL_PREFIX}{token}")


def create_password_reset_token(user_id) -> str:
    token = secrets.token_urlsafe(32)
    client = get_redis_client()
    client.setex(
        f"{PASSWORD_RESET_PREFIX}{token}",
        settings.PASSWORD_RESET_TTL,
        str(user_id),
    )
    return token


def get_user_id_from_password_reset_token(token: str) -> str | None:
    client = get_redis_client()
    user_id = client.get(f"{PASSWORD_RESET_PREFIX}{token}")
    return user_id


def delete_password_reset_token(token: str) -> None:
    client = get_redis_client()
    client.delete(f"{PASSWORD_RESET_PREFIX}{token}")
