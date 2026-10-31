"""
Exponential backoff manager for tracking failed remote instances

Implements progressive retry delays with automatic 24-hour reset:
- Attempt 1: Immediate (0s)
- Attempt 2: 2s delay
- Attempt 3: 4s delay
- Attempt 4: 8s delay
- Attempt 5: 16s delay
- Attempt 6+: 32s delay (maximum)
- Reset: After 24 hours of inactivity
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RemoteInstanceBackoff:
    """Track and manage exponential backoff for failed remote instances/actors"""

    BACKOFF_BASE = 2  # Base multiplier for exponential backoff (seconds)
    MAX_BACKOFF = 32  # Maximum backoff delay (seconds)
    RESET_AFTER = 86400  # Reset after 24 hours (seconds)
    CACHE_PREFIX = "backoff"

    @classmethod
    def _get_cache_key(cls, remote_id: str) -> str:
        """Generate cache key for remote_id"""
        # Use short hash to keep keys manageable
        id_hash = hashlib.sha256(remote_id.encode()).hexdigest()[:16]
        return f"{cls.CACHE_PREFIX}:{id_hash}"

    @classmethod
    def should_skip_fetch(cls, remote_id: str) -> bool:
        """
        Check if we should skip fetching from this remote_id due to backoff

        Returns True if currently in backoff period, False otherwise
        """
        cache_key = cls._get_cache_key(remote_id)
        data = cache.get(cache_key)

        if not data:
            return False

        try:
            backoff_data = json.loads(data)
            next_retry_str = backoff_data.get("next_retry")

            if not next_retry_str:
                return False

            next_retry = datetime.fromisoformat(next_retry_str)
            now = datetime.utcnow()

            # Check if we should reset (24 hours elapsed)
            first_failure_str = backoff_data.get("first_failure")
            if first_failure_str:
                first_failure = datetime.fromisoformat(first_failure_str)
                if (now - first_failure).total_seconds() >= cls.RESET_AFTER:
                    # Auto-reset after 24 hours
                    cache.delete(cache_key)
                    logger.info(f"Auto-reset backoff for {remote_id} after 24 hours")
                    return False

            # Check if still in backoff period
            if now < next_retry:
                logger.debug(
                    f"Skipping fetch for {remote_id}, in backoff until {next_retry}"
                )
                return True

            return False

        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.warning(f"Error parsing backoff data for {remote_id}: {exc}")
            cache.delete(cache_key)
            return False

    @classmethod
    def record_failure(cls, remote_id: str) -> None:
        """
        Record a failed fetch attempt and update backoff schedule

        Increments failure counter and calculates exponential backoff delay
        """
        cache_key = cls._get_cache_key(remote_id)
        data = cache.get(cache_key)
        now = datetime.utcnow()

        if data:
            try:
                backoff_data = json.loads(data)
                failure_count = backoff_data.get("failure_count", 0) + 1
                first_failure = datetime.fromisoformat(
                    backoff_data.get("first_failure", now.isoformat())
                )
            except (json.JSONDecodeError, ValueError):
                failure_count = 1
                first_failure = now
        else:
            failure_count = 1
            first_failure = now

        # Calculate exponential backoff (capped at MAX_BACKOFF)
        backoff_seconds = min(cls.BACKOFF_BASE ** (failure_count - 1), cls.MAX_BACKOFF)
        next_retry = now + timedelta(seconds=backoff_seconds)

        backoff_data = {
            "failure_count": failure_count,
            "last_failure": now.isoformat(),
            "next_retry": next_retry.isoformat(),
            "first_failure": first_failure.isoformat(),
        }

        # Store with 24-hour TTL (auto-cleanup)
        cache.set(cache_key, json.dumps(backoff_data), cls.RESET_AFTER)

        logger.info(
            f"Recorded failure #{failure_count} for {remote_id}, "
            f"next retry in {backoff_seconds}s (at {next_retry})"
        )

    @classmethod
    def record_success(cls, remote_id: str) -> None:
        """
        Clear backoff state after successful fetch

        Removes entry from Redis, allowing immediate future fetches
        """
        cache_key = cls._get_cache_key(remote_id)
        if cache.get(cache_key):
            cache.delete(cache_key)
            logger.info(f"Cleared backoff for {remote_id} after successful fetch")

    @classmethod
    def get_next_retry_time(cls, remote_id: str) -> datetime | None:
        """
        Get the timestamp when we can next attempt to fetch this remote_id

        Returns None if not in backoff
        """
        cache_key = cls._get_cache_key(remote_id)
        data = cache.get(cache_key)

        if not data:
            return None

        try:
            backoff_data = json.loads(data)
            next_retry_str = backoff_data.get("next_retry")
            if next_retry_str:
                return datetime.fromisoformat(next_retry_str)
        except (json.JSONDecodeError, ValueError):
            pass

        return None

    @classmethod
    def cleanup_old_entries(cls) -> int:
        """
        Reset backoff entries older than 24 hours

        This is a periodic task that ensures stale entries are cleaned up.
        Returns number of entries cleaned.

        Note: Redis TTL should handle most cleanup automatically, but this
        provides explicit reset for any entries that might have gotten stuck.
        """
        # In practice, Redis TTL handles this automatically
        # This is a fallback/safety mechanism

        # Django's cache doesn't provide a way to iterate keys efficiently
        # The TTL mechanism should handle cleanup automatically
        # This method is kept as a placeholder for monitoring/debugging

        logger.info("Backoff cleanup task ran (Redis TTL handles automatic cleanup)")
        return 0
