import redis

# 创建全局 Redis 客户端
global_redis_client = redis.Redis(host="124.70.70.96", port=6379, decode_responses=True)

class RedisClient:
    def __init__(self):
        self.redis_client = global_redis_client

    def set_key_value_with_expiry(self, key, value, expiry_seconds):
        self.redis_client.setex(key, expiry_seconds, value)

    def get_value_by_key(self, key):
        return self.redis_client.get(key)


