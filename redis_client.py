import redis

# Connect to the Redis server (running in Docker on port 6379)
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)