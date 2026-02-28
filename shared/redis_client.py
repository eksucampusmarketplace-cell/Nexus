"""Redis client with automatic group namespacing."""

import json
import os
from typing import Any, Optional, Union

import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class GroupScopedRedis:
    """Redis client that automatically namespaces keys by group_id."""

    def __init__(self, redis: aioredis.Redis, group_id: int):
        self._redis = redis
        self._group_id = group_id
        self._prefix = f"nexus:g{group_id}:"

    def _key(self, key: str) -> str:
        """Prefix key with group namespace."""
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Optional[str]:
        """Get a string value."""
        return await self._redis.get(self._key(key))

    async def set(
        self,
        key: str,
        value: Union[str, bytes],
        expire: Optional[int] = None,
    ) -> bool:
        """Set a string value with optional expiration (seconds)."""
        return await self._redis.set(self._key(key), value, ex=expire)

    async def delete(self, key: str) -> int:
        """Delete a key."""
        return await self._redis.delete(self._key(key))

    async def exists(self, key: str) -> int:
        """Check if key exists."""
        return await self._redis.exists(self._key(key))

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key."""
        return await self._redis.expire(self._key(key), seconds)

    async def ttl(self, key: str) -> int:
        """Get remaining TTL of a key."""
        return await self._redis.ttl(self._key(key))

    async def get_json(self, key: str) -> Optional[Any]:
        """Get and parse JSON value."""
        value = await self.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
    ) -> bool:
        """Serialize and set JSON value."""
        return await self.set(key, json.dumps(value), expire)

    async def incr(self, key: str) -> int:
        """Increment a counter."""
        return await self._redis.incr(self._key(key))

    async def incrby(self, key: str, amount: int) -> int:
        """Increment by specific amount."""
        return await self._redis.incrby(self._key(key), amount)

    async def decr(self, key: str) -> int:
        """Decrement a counter."""
        return await self._redis.decr(self._key(key))

    async def sadd(self, key: str, *members: str) -> int:
        """Add members to a set."""
        return await self._redis.sadd(self._key(key), *members)

    async def srem(self, key: str, *members: str) -> int:
        """Remove members from a set."""
        return await self._redis.srem(self._key(key), *members)

    async def smembers(self, key: str) -> set:
        """Get all members of a set."""
        return await self._redis.smembers(self._key(key))

    async def sismember(self, key: str, member: str) -> bool:
        """Check if member exists in set."""
        return await self._redis.sismember(self._key(key), member)

    async def lpush(self, key: str, *values: str) -> int:
        """Push values to the left of a list."""
        return await self._redis.lpush(self._key(key), *values)

    async def rpush(self, key: str, *values: str) -> int:
        """Push values to the right of a list."""
        return await self._redis.rpush(self._key(key), *values)

    async def lrange(self, key: str, start: int, end: int) -> list:
        """Get range of list elements."""
        return await self._redis.lrange(self._key(key), start, end)

    async def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim list to specified range."""
        return await self._redis.ltrim(self._key(key), start, end)

    async def hset(self, key: str, field: str, value: str) -> int:
        """Set hash field."""
        return await self._redis.hset(self._key(key), field, value)

    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field."""
        return await self._redis.hget(self._key(key), field)

    async def hgetall(self, key: str) -> dict:
        """Get all hash fields."""
        return await self._redis.hgetall(self._key(key))

    async def hdel(self, key: str, *fields: str) -> int:
        """Delete hash fields."""
        return await self._redis.hdel(self._key(key), *fields)

    async def zadd(self, key: str, mapping: dict) -> int:
        """Add to sorted set."""
        return await self._redis.zadd(self._key(key), mapping)

    async def zrange(
        self,
        key: str,
        start: int,
        end: int,
        withscores: bool = False,
    ) -> list:
        """Get range from sorted set."""
        return await self._redis.zrange(
            self._key(key), start, end, withscores=withscores
        )

    async def zrevrange(
        self,
        key: str,
        start: int,
        end: int,
        withscores: bool = False,
    ) -> list:
        """Get reverse range from sorted set."""
        return await self._redis.zrevrange(
            self._key(key), start, end, withscores=withscores
        )

    async def zscore(self, key: str, member: str) -> Optional[float]:
        """Get score of member in sorted set."""
        return await self._redis.zscore(self._key(key), member)

    async def zrem(self, key: str, *members: str) -> int:
        """Remove members from sorted set."""
        return await self._redis.zrem(self._key(key), *members)

    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel (group-scoped)."""
        return await self._redis.publish(self._key(channel), message)

    async def keys(self, pattern: str) -> list:
        """Get keys matching pattern (within group namespace)."""
        return await self._redis.keys(self._key(pattern))

    async def flush_group(self) -> int:
        """Delete all keys in this group's namespace."""
        keys = await self.keys("*")
        if keys:
            return await self._redis.delete(*keys)
        return 0


# Global Redis connection pool
_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Get or create global Redis connection."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool


async def get_group_redis(group_id: int) -> GroupScopedRedis:
    """Get group-scoped Redis client."""
    redis = await get_redis()
    return GroupScopedRedis(redis, group_id)


async def close_redis() -> None:
    """Close global Redis connection."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None


class RateLimiter:
    """Token bucket rate limiter using Redis."""

    def __init__(self, redis: GroupScopedRedis):
        self._redis = redis

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> tuple[bool, int, int]:
        """
        Check if action is allowed under rate limit.
        Returns: (allowed, remaining, reset_in)
        """
        bucket_key = f"ratelimit:{key}"
        now = await self._redis._redis.time()
        current_time = int(now[0])

        pipe = self._redis._redis.pipeline()
        pipe.hgetall(self._redis._key(bucket_key))
        result = await pipe.execute()

        bucket = result[0]

        if not bucket:
            # New bucket
            await self._redis.hset(bucket_key, "tokens", str(limit - 1))
            await self._redis.hset(bucket_key, "reset_at", str(current_time + window))
            await self._redis.expire(bucket_key, window)
            return True, limit - 1, window

        tokens = int(bucket.get(b"tokens", b"0"))
        reset_at = int(bucket.get(b"reset_at", b"0"))

        if current_time >= reset_at:
            # Reset bucket
            await self._redis.hset(bucket_key, "tokens", str(limit - 1))
            await self._redis.hset(bucket_key, "reset_at", str(current_time + window))
            return True, limit - 1, window

        if tokens > 0:
            # Consume token
            await self._redis.hset(bucket_key, "tokens", str(tokens - 1))
            remaining = tokens - 1
            reset_in = reset_at - current_time
            return True, remaining, reset_in

        # Rate limited
        reset_in = reset_at - current_time
        return False, 0, reset_in
