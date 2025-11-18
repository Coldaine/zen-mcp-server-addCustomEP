"""Redis checkpoint configuration for LangGraph state persistence."""

import logging
import os
from typing import Optional

from langgraph.checkpoint.redis import RedisSaver
from redis import Redis

logger = logging.getLogger(__name__)


def create_redis_checkpointer() -> Optional[RedisSaver]:
    """Create Redis checkpointer for LangGraph state persistence.

    Returns:
        RedisSaver instance or None if Redis is not configured
    """
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_db = int(os.getenv("REDIS_DB", 0))
    redis_password = os.getenv("REDIS_PASSWORD")

    try:
        # Initialize Redis client
        redis_client = Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=False,  # Keep bytes for checkpoint data
        )

        # Test connection
        redis_client.ping()
        logger.info(f"Connected to Redis at {redis_host}:{redis_port}")

        # Create checkpointer
        checkpointer = RedisSaver(redis_client)
        return checkpointer

    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}")
        logger.warning("Running without state persistence (in-memory only)")
        return None
