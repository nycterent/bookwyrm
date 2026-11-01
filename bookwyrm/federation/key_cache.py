"""
Cache remote user public keys for signature verification

Caches user IDs mapped to actor URLs, allowing fast signature verification
without repeated HTTP fetches to remote instances.
"""

import hashlib
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

KEY_CACHE_TTL = 86400  # 24 hours in seconds


def get_cache_key(actor_url: str) -> str:
    """
    Generate cache key for actor URL

    Uses short hash to keep Redis keys manageable
    """
    url_hash = hashlib.sha256(actor_url.encode()).hexdigest()[:16]
    return f"pubkey:{url_hash}"


def get_cached_public_key(actor_url: str):
    """
    Get cached remote user for signature verification

    Returns User object if cached, None otherwise
    """
    from bookwyrm import models

    cache_key = get_cache_key(actor_url)
    user_id = cache.get(cache_key)

    if user_id:
        try:
            user = models.User.objects.get(id=user_id)
            logger.debug(f"Cache hit for actor {actor_url} (user_id={user_id})")
            return user
        except models.User.DoesNotExist:
            # Cached ID no longer valid (user deleted?)
            logger.warning(f"Cached user {user_id} for {actor_url} no longer exists")
            cache.delete(cache_key)

    logger.debug(f"Cache miss for actor {actor_url}")
    return None


def cache_public_key(actor_url: str, user) -> None:
    """
    Cache remote user's ID for signature verification

    Stores user ID (not full object) with 24-hour TTL
    """
    cache_key = get_cache_key(actor_url)
    cache.set(cache_key, user.id, KEY_CACHE_TTL)
    logger.info(f"Cached public key for {actor_url} (user_id={user.id}, TTL=24h)")


def clear_cached_key(actor_url: str) -> None:
    """
    Clear cached key for actor

    Called when signature verification fails, as key might be stale
    """
    cache_key = get_cache_key(actor_url)
    if cache.get(cache_key):
        cache.delete(cache_key)
        logger.info(
            f"Cleared cached key for {actor_url} (signature verification failed)"
        )
