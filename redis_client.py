import os
import redis

# Read Redis host from environment (set by docker-compose), default to localhost
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

# Connect to the Redis server
redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)